import copy
import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from integrations import Services
from server import create_app
from tests.fixtures import FakeServices

HEADERS = {"X-Tutor-Request": "1"}


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.sqlite"
        self.services = FakeServices()
        self.app = create_app(self.path, self.services)
        self.client = TestClient(self.app, headers=HEADERS)
        self.addCleanup(self.client.close)
        self.client.post("/api/session")

    def chat(self, **kwargs):
        result = self.client.post("/api/chats", json={"lesson_id": "demo-grounding", **kwargs})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()["id"]

    def ask(self, chat, text="Citation là gì?", request_id="request-0001", client=None):
        return (client or self.client).post(f"/api/chats/{chat}/messages", json={"text": text, "client_request_id": request_id})

    def test_session_required_and_csrf_header(self):
        with TestClient(self.app) as other:
            self.assertEqual(other.get("/api/lessons").status_code, 401)
            self.assertEqual(other.post("/api/session").status_code, 403)
        response = self.client.post("/api/session")
        self.assertTrue(response.json()["fixture_mode"])

    def test_cookie_and_security_headers(self):
        with TestClient(self.app, headers=HEADERS) as other:
            r = other.post("/api/session")
            self.assertIn("HttpOnly", r.headers["set-cookie"])
            self.assertIn("SameSite=strict", r.headers["set-cookie"])
            self.assertIn("frame-ancestors 'none'", r.headers["content-security-policy"])

    def test_refresh_persistence_and_real_source_locator(self):
        chat = self.chat()
        self.assertEqual(self.ask(chat).status_code, 200)
        restored = self.client.get(f"/api/chats/{chat}").json()
        self.assertEqual(len(restored["messages"]), 2)
        source = self.client.get(f"/api/sources/sample-01?chat_id={chat}")
        self.assertEqual(source.json()["locator"], "1")
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM turns WHERE status='complete'").fetchone()[0], 1)

    def test_other_session_cannot_read_chat_or_source(self):
        chat = self.chat()
        with TestClient(self.app, headers=HEADERS) as other:
            other.post("/api/session")
            self.assertEqual(other.get(f"/api/chats/{chat}").status_code, 404)
            self.assertEqual(other.get(f"/api/sources/sample-01?chat_id={chat}").status_code, 404)
            self.assertEqual(self.ask(chat, client=other).status_code, 404)

    def test_snapshot_immutable_across_edits_and_new_chat(self):
        chat = self.chat()
        saved = self.client.put("/api/persona", json={"text": "Ngắn gọn", "expected_version": 1})
        self.assertEqual(saved.json()["version"], 2)
        self.ask(chat)
        old_input = [c[4] for c in self.services.calls if c[0] == "ai"][-1]
        self.assertEqual(old_input["persona"]["version"], 1)
        second = self.chat()
        self.ask(second)
        new_input = [c[4] for c in self.services.calls if c[0] == "ai"][-1]
        self.assertEqual(new_input["persona"]["text"], "Ngắn gọn")

    def test_empty_persona_and_explicit_opt_out(self):
        self.client.put("/api/persona", json={"text": "", "expected_version": 1})
        chat = self.chat()
        self.assertEqual(self.ask(chat).status_code, 200)
        opt_out = self.chat(without_persona=True)
        self.assertIsNone(self.client.get(f"/api/chats/{opt_out}").json()["persona_version"])

    def test_duplicate_retry_returns_same_result(self):
        chat = self.chat()
        first = self.ask(chat)
        second = self.ask(chat)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(len([c for c in self.services.calls if c[0] == "ai"]), 1)
        self.assertEqual(self.ask(chat, text="Khác").status_code, 409)

    def test_concurrent_submission_locked_per_chat(self):
        chat = self.chat()
        self.services.release = threading.Event()
        with ThreadPoolExecutor(max_workers=2) as pool:
            future = pool.submit(self.ask, chat)
            self.assertTrue(self.services.entered.wait(3))
            self.assertEqual(self.ask(chat, request_id="request-0002").status_code, 409)
            self.services.release.set()
            self.assertEqual(future.result().status_code, 200)

    def test_failed_turn_can_retry_without_duplicate_user_message(self):
        chat = self.chat()
        self.services.failure = HTTPException(504, "timeout")
        self.assertEqual(self.ask(chat).status_code, 504)
        self.services.failure = None
        self.assertEqual(self.ask(chat).status_code, 200)
        self.assertEqual(len(self.client.get(f"/api/chats/{chat}").json()["messages"]), 2)

    def test_history_comes_from_stored_chat(self):
        chat = self.chat()
        self.ask(chat)
        self.ask(chat, "Ngắn hơn", "request-0002")
        history = [c[4]["history"] for c in self.services.calls if c[0] == "ai"][-1]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["text"], "Citation là gì?")

    def test_invalid_or_missing_citation_is_not_an_answer(self):
        for citations in [[], [{"source_id": "made-up", "locator": "1"}], [{"source_id": "sample-01", "locator": "999"}]]:
            with self.subTest(citations=citations):
                self.services.reply_override = {"decision": "answer", "text": "bad", "citations": citations}
                self.assertEqual(self.ask(self.chat()).status_code, 502)

    def test_invalid_decision_and_unsafe_action_rejected(self):
        for reply in [{"decision": "oops", "text": "bad"}, {"decision": "clarify", "text": "bad", "actions": [{"label": "Run", "type": "javascript", "value": "alert(1)"}]}, {"decision": "clarify", "text": "bad", "actions": [{"label": "Open", "type": "open_source", "value": "unknown"}]}]:
            self.services.reply_override = reply
            self.assertEqual(self.ask(self.chat()).status_code, 502)

    def test_question_validation_and_no_client_snapshot(self):
        chat = self.chat()
        for payload in [{"text": "  ", "client_request_id": "request-0001"}, {"text": "x" * 4001, "client_request_id": "request-0001"}, {"text": "x", "client_request_id": "request-0001", "persona": {"text": "override"}}, {"text": "x", "client_request_id": "request-0001", "selected_source_ids": ["unknown"]}]:
            self.assertEqual(self.client.post(f"/api/chats/{chat}/messages", json=payload).status_code, 422)

    def test_proposal_does_not_save_until_accept_and_undo(self):
        chat = self.chat()
        proposal = self.ask(chat, "Ghi nhớ ví dụ").json()["persona_proposals"][0]
        self.assertEqual(self.client.get("/api/persona").json()["version"], 1)
        result = self.client.post(f"/api/persona/proposals/{proposal['id']}/accept", json={"expected_version": 1, "edited_text": "Đã sửa"})
        self.assertEqual(result.json()["text"], "Đã sửa")
        self.assertEqual(self.client.get(f"/api/chats/{chat}").json()["persona_version"], 1)
        undo = self.client.post("/api/persona/undo", json={"target_version": 1, "expected_version": 2})
        self.assertEqual(undo.json()["version"], 3)
        self.assertNotEqual(undo.json()["text"], "Đã sửa")

    def test_proposal_reject_and_owner_boundary(self):
        chat = self.chat()
        proposal = self.ask(chat, "Ghi nhớ ví dụ").json()["persona_proposals"][0]
        with TestClient(self.app, headers=HEADERS) as other:
            other.post("/api/session")
            self.assertEqual(other.post(f"/api/persona/proposals/{proposal['id']}/accept", json={"expected_version": 1}).status_code, 404)
        rejected = self.client.post(f"/api/persona/proposals/{proposal['id']}/reject", json={})
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(self.client.get("/api/persona").json()["version"], 1)
        self.assertEqual(self.client.post(f"/api/persona/proposals/{proposal['id']}/accept", json={"expected_version": 1}).status_code, 409)

    def test_conflict_and_persona_limits(self):
        self.assertEqual(self.client.put("/api/persona", json={"text": "x", "expected_version": 0}).status_code, 409)
        self.assertEqual(self.client.put("/api/persona", json={"text": "x" * 2001, "expected_version": 1}).status_code, 422)

    def test_clear_memory_forwards_and_preserves_chat(self):
        chat = self.chat()
        result = self.client.request("DELETE", "/api/persona/memory", json={"expected_version": 1})
        self.assertEqual(result.json()["version"], 2)
        self.assertEqual(self.client.get(f"/api/chats/{chat}").json()["persona_version"], 1)

    def test_missing_services_do_not_fall_back_to_fake_ai(self):
        app = create_app(Path(self.temp.name) / "disabled.sqlite", Services())
        with TestClient(app, headers=HEADERS) as client:
            caps = client.post("/api/session").json()
            self.assertFalse(caps["fixture_mode"])
            self.assertFalse(caps["ai_connected"])
            chat = client.post("/api/chats", json={"lesson_id": "demo-grounding"}).json()["id"]
            self.assertEqual(self.ask(chat, client=client).status_code, 503)
            self.assertEqual(client.get("/api/persona").status_code, 503)

    def test_persona_failure_does_not_silently_drop_snapshot(self):
        self.services.failure = HTTPException(502, "upstream")
        self.assertEqual(self.client.post("/api/chats", json={"lesson_id": "demo-grounding"}).status_code, 502)
        self.chat(without_persona=True)

    def test_foreign_source_and_recovery_after_restart(self):
        chat = self.chat()
        with closing(sqlite3.connect(self.path)) as db:
            body = json.dumps({"text": "x", "client_request_id": "request-0001", "selected_source_ids": []}, sort_keys=True)
            db.execute("INSERT INTO turns VALUES ('interrupted',?,?,?,'pending',NULL,NULL,1)", (chat, "request-0001", body))
            db.commit()
        restarted = create_app(self.path, self.services)
        with TestClient(restarted, headers=HEADERS, cookies=dict(self.client.cookies)) as client:
            self.assertEqual(client.get(f"/api/chats/{chat}").json()["messages"][0]["status"], "failed")
        self.assertEqual(self.client.get(f"/api/sources/unknown?chat_id={chat}").status_code, 404)


class TransportTests(unittest.TestCase):
    def test_http_contract_identity_and_auth(self):
        def handler(request):
            self.assertEqual(request.url.path, "/respond")
            self.assertEqual(request.headers["X-Learner-ID"], "server-owner")
            self.assertEqual(request.headers["Authorization"], "Bearer test-only")
            self.assertEqual(request.headers["Idempotency-Key"], "turn-id")
            return httpx.Response(200, json={"text": "ok"})
        original = httpx.Client
        with patch("integrations.httpx.Client", side_effect=lambda **kw: original(transport=httpx.MockTransport(handler), **kw)):
            result = Services("http://ai.test", "", "test-only").request("ai", "POST", "/respond", "server-owner", {}, "turn-id")
            self.assertEqual(result, {"text": "ok"})

    def test_transport_timeout_and_invalid_json(self):
        for timeout in (False, True):
            def handler(request):
                if timeout:
                    raise httpx.ReadTimeout("timeout")
                return httpx.Response(200, text="not json")
            original = httpx.Client
            with patch("integrations.httpx.Client", side_effect=lambda **kw: original(transport=httpx.MockTransport(handler), **kw)):
                with self.assertRaises(HTTPException) as caught:
                    Services("http://ai.test").request("ai", "POST", "/respond", "owner", {})
                self.assertEqual(caught.exception.status_code, 504 if timeout else 502)


if __name__ == "__main__":
    unittest.main()
