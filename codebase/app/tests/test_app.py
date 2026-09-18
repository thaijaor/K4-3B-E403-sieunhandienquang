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
from integrations import Services, ContractError
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
        source = self.client.get(f"/api/sources/demo-grounding--kiem-chung?chat_id={chat}")
        self.assertEqual(source.json()["locator"], "mock-lessons/demo-grounding.md#kiem-chung")
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM turns WHERE status='complete'").fetchone()[0], 1)

    def test_other_session_cannot_read_chat_or_source(self):
        chat = self.chat()
        with TestClient(self.app, headers=HEADERS) as other:
            other.post("/api/session")
            self.assertEqual(other.get(f"/api/chats/{chat}").status_code, 404)
            self.assertEqual(other.get(f"/api/sources/demo-grounding--kiem-chung?chat_id={chat}").status_code, 404)
            self.assertEqual(self.ask(chat, client=other).status_code, 404)

    def test_persona_is_not_snapshotted_into_chat(self):
        chat = self.chat()
        self.assertFalse([c for c in self.services.calls if c[0] == "persona"])
        self.assertEqual(self.client.put("/api/persona", json={"text": "Ngắn gọn"}).json()["text"], "Ngắn gọn")
        self.ask(chat)
        self.assertNotIn("persona", [c[4] for c in self.services.calls if c[0] == "ai"][-1])
        self.assertNotIn("persona_version", self.client.get(f"/api/chats/{chat}").json())
        self.assertEqual(self.client.post("/api/chats", json={"lesson_id": "demo-grounding", "without_persona": True}).status_code, 422)

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
        for citations in [[], [{"source_id": "made-up", "locator": "1"}], [{"source_id": "demo-grounding--kiem-chung", "locator": "999"}]]:
            with self.subTest(citations=citations):
                self.services.reply_override = {"decision": "answer", "text": "bad", "citations": citations}
                self.assertEqual(self.ask(self.chat()).status_code, 502)

    def test_chat_reply_needs_no_citation(self):
        self.services.reply_override = {"decision": "chat", "text": "Chào bạn!"}
        response = self.ask(self.chat())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["decision"], "chat")

    def test_invalid_decision_and_unsafe_action_rejected(self):
        for reply in [{"decision": "oops", "text": "bad"}, {"decision": "clarify", "text": "bad", "actions": [{"label": "Run", "type": "javascript", "value": "alert(1)"}]}, {"decision": "clarify", "text": "bad", "actions": [{"label": "Open", "type": "open_source", "value": "unknown"}]}]:
            self.services.reply_override = reply
            self.assertEqual(self.ask(self.chat()).status_code, 502)

    def test_question_validation_and_no_client_snapshot(self):
        chat = self.chat()
        for payload in [{"text": "  ", "client_request_id": "request-0001"}, {"text": "x" * 4001, "client_request_id": "request-0001"}, {"text": "x", "client_request_id": "request-0001", "persona": {"text": "override"}}, {"text": "x", "client_request_id": "request-0001", "selected_source_ids": ["unknown"]}]:
            self.assertEqual(self.client.post(f"/api/chats/{chat}/messages", json=payload).status_code, 422)

    def test_proposal_does_not_save_until_accept(self):
        chat = self.chat()
        before = self.client.get("/api/persona").json()["text"]
        proposal = self.ask(chat, "Ghi nhớ ví dụ").json()["persona_proposals"][0]
        self.assertEqual(self.client.get("/api/persona").json()["text"], before)
        result = self.client.post(f"/api/persona/proposals/{proposal['id']}/accept", json={"edited_text": "Đã sửa"})
        self.assertEqual(result.json()["text"], "Đã sửa")
        self.assertEqual(self.client.get(f"/api/chats/{chat}").json()["messages"][1]["persona_proposals"][0]["status"], "accepted")
        self.assertEqual(self.client.post("/api/persona/undo", json={}).status_code, 404)

    def test_proposal_reject_and_owner_boundary(self):
        chat = self.chat()
        proposal = self.ask(chat, "Ghi nhớ ví dụ").json()["persona_proposals"][0]
        with TestClient(self.app, headers=HEADERS) as other:
            other.post("/api/session")
            self.assertEqual(other.post(f"/api/persona/proposals/{proposal['id']}/accept", json={}).status_code, 404)
        before = self.client.get("/api/persona").json()["text"]
        rejected = self.client.post(f"/api/persona/proposals/{proposal['id']}/reject", json={})
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(self.client.get("/api/persona").json()["text"], before)
        self.assertEqual(self.client.post(f"/api/persona/proposals/{proposal['id']}/accept", json={}).status_code, 409)

    def test_persona_limits(self):
        self.assertEqual(self.client.put("/api/persona", json={"text": "x" * 2001}).status_code, 422)
        self.assertEqual(self.client.put("/api/persona", json={"text": "x", "expected_version": 1}).status_code, 422)

    def test_clear_memory_forwards(self):
        self.client.put("/api/persona", json={"text": "tuỳ chỉnh"})
        result = self.client.delete("/api/persona/memory")
        self.assertEqual(result.status_code, 200)
        self.assertIn("## Tutor nhớ về bạn", result.json()["text"])

    def test_proposals_dropped_without_persona_service(self):
        self.services.persona_url = ""
        self.services.reply_override = {"decision": "chat", "text": "Ok", "persona_proposals": [{"id": "p-1", "before": "a", "after": "b"}]}
        response = self.ask(self.chat())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["persona_proposals"], [])

    def test_missing_services_do_not_fall_back_to_fake_ai(self):
        app = create_app(Path(self.temp.name) / "disabled.sqlite", Services())
        with TestClient(app, headers=HEADERS) as client:
            caps = client.post("/api/session").json()
            self.assertFalse(caps["fixture_mode"])
            self.assertFalse(caps["ai_connected"])
            chat = client.post("/api/chats", json={"lesson_id": "demo-grounding"}).json()["id"]
            self.assertEqual(self.ask(chat, client=client).status_code, 503)
            self.assertEqual(client.get("/api/persona").status_code, 503)

    def test_persona_failure_does_not_block_new_chat(self):
        self.services.failure = HTTPException(502, "upstream")
        self.assertEqual(self.client.post("/api/chats", json={"lesson_id": "demo-grounding"}).status_code, 200)
        self.assertEqual(self.client.get("/api/persona").status_code, 502)

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

    def test_markdown_catalog_and_stable_citation_anchors(self):
        lessons = self.client.get('/api/lessons').json()
        self.assertEqual(len(lessons), 6)
        self.assertEqual(len({x['day'] for x in lessons}), 3)
        source_ids = []
        for lesson in lessons:
            content = self.client.get('/api/lessons/' + lesson['id']).json()
            self.assertTrue(content['markdown'].endswith('.md'))
            self.assertTrue(content['sample'])
            for source in content['sources']:
                self.assertEqual(source['kind'], 'markdown')
                self.assertEqual(source['locator'], content['markdown'] + '#' + source['anchor'])
                self.assertTrue(source['text'])
                source_ids.append(source['id'])
            chat = self.client.post('/api/chats', json={'lesson_id': lesson['id']}).json()['id']
            reply = self.ask(chat)
            self.assertEqual(reply.status_code, 200, reply.text)
            citation = reply.json()['citations'][0]
            opened = self.client.get(f"/api/sources/{citation['source_id']}?chat_id={chat}")
            self.assertEqual(opened.json()['locator'], citation['locator'])
        self.assertEqual(len(source_ids), len(set(source_ids)))

    def test_chat_history_owner_and_order(self):
        first, second = self.chat(), self.chat()
        history = self.client.get('/api/chats').json()
        self.assertEqual([x['id'] for x in history], [second, first])
        self.assertTrue(history[0]['title'])
        self.assertNotIn('persona', history[0])
        with TestClient(self.app, headers=HEADERS) as other:
            self.assertEqual(other.get('/api/chats').status_code, 401)
            other.post('/api/session')
            self.assertEqual(other.get('/api/chats').json(), [])

    def test_retry_contract_failure_rotates_persisted_key(self):
        chat = self.chat()
        self.services.reply_override = {'decision': 'answer', 'text': 'Missing citation'}
        self.assertEqual(self.ask(chat).status_code, 502)
        failed_key = [c[5] for c in self.services.calls if c[0] == 'ai'][-1]
        self.services.reply_override = None
        # Simulate an upstream caching bad output by idempotency key.
        original = self.services.request
        def cached(kind, method, path, owner, payload=None, request_id=None):
            if kind == 'ai' and request_id == failed_key:
                return {'decision': 'answer', 'text': 'Cached invalid reply'}
            return original(kind, method, path, owner, payload, request_id)
        restarted = create_app(self.path, self.services)
        with patch.object(self.services, 'request', side_effect=cached):
            with TestClient(restarted, headers=HEADERS, cookies=dict(self.client.cookies)) as client:
                self.assertEqual(self.ask(chat, client=client).status_code, 200)
        calls = [c for c in self.services.calls if c[0] == 'ai']
        self.assertNotEqual(calls[-1][5], failed_key)
        self.assertEqual(calls[-1][4]['request_id'], calls[-1][5])
        self.assertEqual(len(self.client.get(f'/api/chats/{chat}').json()['messages']), 2)

    def test_retry_timeout_preserves_key(self):
        chat = self.chat()
        self.services.failure = HTTPException(504, 'timeout')
        self.assertEqual(self.ask(chat).status_code, 504)
        self.services.failure = None
        self.assertEqual(self.ask(chat).status_code, 200)
        keys = [c[5] for c in self.services.calls if c[0] == 'ai']
        self.assertEqual(keys[0], keys[1])

    def test_retry_invalid_json_rotates_key(self):
        chat = self.chat()
        self.services.failure = ContractError('Invalid JSON')
        self.assertEqual(self.ask(chat).status_code, 502)
        self.services.failure = None
        self.assertEqual(self.ask(chat).status_code, 200)
        keys = [c[5] for c in self.services.calls if c[0] == 'ai']
        self.assertNotEqual(keys[0], keys[1])

    def test_old_failed_turn_cannot_retry_after_new_question(self):
        chat = self.chat()
        self.services.failure = HTTPException(504, 'timeout')
        self.ask(chat)
        self.services.failure = None
        self.assertEqual(self.ask(chat, 'Q2', 'request-0002').status_code, 200)
        count = len(self.services.calls)
        self.assertEqual(self.ask(chat).status_code, 409)
        self.assertEqual(len(self.services.calls), count)
        messages = self.client.get(f'/api/chats/{chat}').json()['messages']
        self.assertFalse(messages[0]['retryable'])
        self.assertEqual(messages[1]['text'], 'Q2')

    def test_unexpected_exception_does_not_leave_pending_turn(self):
        for failure in [KeyError('locator'), RuntimeError('unexpected')]:
            chat = self.chat()
            self.services.failure = failure
            self.assertEqual(self.ask(chat).status_code, 500)
            messages = self.client.get(f'/api/chats/{chat}').json()['messages']
            self.assertEqual(messages[0]['status'], 'failed')
            self.services.failure = None
            self.assertEqual(self.ask(chat).status_code, 200)

    def test_database_failure_at_completion_and_cleanup_recovers(self):
        chat = self.chat()
        original_connect = sqlite3.connect
        class LockedOnce(sqlite3.Connection):
            completion_failed = False
            cleanup_failed = False
            def execute(self, sql, parameters=()):
                if "SET status='complete'" in sql and not self.completion_failed:
                    LockedOnce.completion_failed = True
                    raise sqlite3.OperationalError('database is locked')
                if "SET status='failed'" in sql and not self.cleanup_failed:
                    LockedOnce.cleanup_failed = True
                    raise sqlite3.OperationalError('database is locked')
                return super().execute(sql, parameters)
        with patch('server.sqlite3.connect', side_effect=lambda *a, **kw: original_connect(*a, **kw, factory=LockedOnce)):
            self.assertEqual(self.ask(chat).status_code, 500)
            messages = self.client.get(f'/api/chats/{chat}').json()['messages']
            self.assertEqual(messages[0]['status'], 'failed')
            self.assertEqual(self.ask(chat).status_code, 200)
        self.assertTrue(LockedOnce.completion_failed and LockedOnce.cleanup_failed)

    def test_preview_memory_proposal_in_correct_section(self):
        chat = self.chat()
        proposal = self.ask(chat, 'Ghi nhớ ví dụ').json()['persona_proposals'][0]
        remembered = proposal['after'].split('## Tutor nhớ về bạn')[1]
        self.assertIn('Ưu tiên ví dụ', remembered)
        self.assertNotIn('## Không được nhớ', proposal['after'])
        result = self.client.post(f"/api/persona/proposals/{proposal['id']}/accept", json={})
        self.assertEqual(result.json()['text'], proposal['after'])


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
                with self.assertRaises(HTTPException if timeout else ContractError) as caught:
                    Services("http://ai.test").request("ai", "POST", "/respond", "owner", {})
                if timeout:
                    self.assertEqual(caught.exception.status_code, 504)


if __name__ == "__main__":
    unittest.main()
