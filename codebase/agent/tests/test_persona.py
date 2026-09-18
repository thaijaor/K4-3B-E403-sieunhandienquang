import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from fastapi.testclient import TestClient

from app import create_app
from persona.store import DEFAULT_TEXT, PersonaStore, add_item, clear_section, section_items

FIXTURES = Path(__file__).parent / "fixtures" / "lessons.json"
BODY = {"request_id": "req-1", "chat_id": "chat-1", "lesson_id": "demo", "text": "từ nay trả lời ngắn gọn thôi nha"}


def call(name, arguments, call_id="call-1"):
    return SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=json.dumps(arguments, ensure_ascii=False)))


class ScriptedLLM:
    model = "fake"

    def __init__(self, *messages):
        self.messages = list(messages)
        self.calls = []

    def complete(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        return self.messages.pop(0)


class TextEditTest(unittest.TestCase):
    def test_add_item_into_empty_section(self):
        after = add_item(DEFAULT_TEXT, "Tutor nhớ về bạn", "Chưa quen lập trình")
        self.assertEqual(section_items(after, "Tutor nhớ về bạn"), ["Chưa quen lập trình"])
        self.assertEqual(section_items(after, "Tính cách Tutor"), ["Xưng hô: mình – bạn"])
        self.assertNotIn("## Không được nhớ", after)

    def test_key_value_item_replaces_same_key(self):
        after = add_item(DEFAULT_TEXT, "Tính cách Tutor", "Xưng hô: anh – em")
        self.assertEqual(section_items(after, "Tính cách Tutor"), ["Xưng hô: anh – em"])

    def test_duplicate_item_is_noop(self):
        once = add_item(DEFAULT_TEXT, "Tutor nhớ về bạn", "Thích ví dụ")
        self.assertEqual(add_item(once, "Tutor nhớ về bạn", "thích ví dụ"), once)

    def test_clear_section_keeps_others(self):
        text = add_item(DEFAULT_TEXT, "Tutor nhớ về bạn", "Chưa quen lập trình")
        cleared = clear_section(text, "Tutor nhớ về bạn")
        self.assertEqual(section_items(cleared, "Tutor nhớ về bạn"), [])
        self.assertEqual(section_items(cleared, "Tính cách Tutor"), ["Xưng hô: mình – bạn"])


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = PersonaStore(Path(self.tmp.name) / "p.sqlite")

    def tearDown(self):
        self.tmp.cleanup()

    def test_accept_applies_to_current_text_not_stale_after(self):
        proposal = self.store.propose("a", "Tutor nhớ về bạn", "Chưa quen lập trình")
        self.store.save("a", add_item(DEFAULT_TEXT, "Tính cách Tutor", "Độ dài: ngắn gọn"))  # học viên sửa tay sau đó
        text = self.store.accept("a", proposal["id"])["text"]
        self.assertIn("Độ dài: ngắn gọn", text)
        self.assertIn("Chưa quen lập trình", text)

    def test_accept_is_idempotent_and_edited_text_wins(self):
        proposal = self.store.propose("a", "Tutor nhớ về bạn", "Thích ví dụ")
        self.assertEqual(self.store.accept("a", proposal["id"], "Bản tự sửa")["text"], "Bản tự sửa")
        self.assertEqual(self.store.accept("a", proposal["id"])["text"], "Bản tự sửa")

    def test_reject_does_not_change_persona(self):
        proposal = self.store.propose("a", "Tutor nhớ về bạn", "Thích ví dụ")
        self.store.reject("a", proposal["id"])
        self.assertEqual(self.store.get("a")["text"], DEFAULT_TEXT)
        self.assertEqual(self.store.accept("a", proposal["id"])["text"], DEFAULT_TEXT)

    def test_dont_remember_topic_is_not_proposed(self):
        self.store.save("a", add_item(DEFAULT_TEXT, "Tutor nhớ về bạn", "Đừng nhớ: điểm số"))
        self.assertIsNone(self.store.propose("a", "Tutor nhớ về bạn", "Lo lắng về điểm số"))
        self.assertIsNotNone(self.store.propose("a", "Tutor nhớ về bạn", "Thích ví dụ"))

    def test_dont_remember_lines_do_not_replace_each_other(self):
        self.store.save("a", add_item(DEFAULT_TEXT, "Tutor nhớ về bạn", "Đừng nhớ: điểm số"))
        proposal = self.store.propose("a", "Tutor nhớ về bạn", "Đừng nhớ: giờ học")
        items = section_items(self.store.accept("a", proposal["id"])["text"], "Tutor nhớ về bạn")
        self.assertEqual(items, ["Đừng nhớ: điểm số", "Đừng nhớ: giờ học"])

    def test_owner_isolation(self):
        proposal = self.store.propose("a", "Tutor nhớ về bạn", "Thích ví dụ")
        with self.assertRaises(KeyError):
            self.store.accept("b", proposal["id"])


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def client(self, llm):
        with mock.patch.dict(os.environ, {"SERVICE_API_KEY": ""}):
            return TestClient(create_app(llm=llm, lessons_file=FIXTURES, env_file=None, db_path=Path(self.tmp.name) / "p.sqlite"))

    def test_routes(self):
        client = self.client(ScriptedLLM())
        learner = {"X-Learner-ID": "a"}
        self.assertEqual(client.get("/persona").status_code, 400)
        self.assertEqual(client.get("/persona", headers=learner).json()["text"], DEFAULT_TEXT)
        self.assertEqual(client.put("/persona", json={"text": "Ngắn gọn"}, headers=learner).json()["text"], "Ngắn gọn")
        self.assertEqual(client.put("/persona", json={"text": "x" * 2001}, headers=learner).status_code, 422)
        self.assertEqual(client.get("/persona", headers={"X-Learner-ID": "b"}).json()["text"], DEFAULT_TEXT)
        self.assertEqual(client.post("/persona/proposals/nope/accept", json={}, headers=learner).status_code, 404)

    def test_respond_returns_proposal_from_tool_call(self):
        llm = ScriptedLLM(
            SimpleNamespace(content="", tool_calls=[call("propose_persona_memory", {"section": "Tính cách Tutor", "item": "Độ dài: ngắn gọn"})]),
            SimpleNamespace(content="Ok, mình sẽ trả lời ngắn.", tool_calls=None))
        client = self.client(llm)
        reply = client.post("/respond", json=BODY, headers={"X-Learner-ID": "a"}).json()
        self.assertEqual(reply["text"], "Ok, mình sẽ trả lời ngắn.")
        self.assertEqual(len(reply["persona_proposals"]), 1)
        self.assertIn("Độ dài: ngắn gọn", reply["persona_proposals"][0]["after"])
        self.assertIn("tools", llm.calls[0][1])
        self.assertNotIn("tools", llm.calls[1][1])
        self.assertIn("</persona>", llm.calls[0][0][0]["content"])
        self.assertEqual(client.get("/persona", headers={"X-Learner-ID": "a"}).json()["text"], DEFAULT_TEXT)

    def test_edit_applies_to_next_question(self):
        llm = ScriptedLLM(SimpleNamespace(content="Ok", tool_calls=None))
        client = self.client(llm)
        client.put("/persona", json={"text": "Độ dài: ngắn gọn"}, headers={"X-Learner-ID": "a"})
        client.post("/respond", json=BODY, headers={"X-Learner-ID": "a"})
        self.assertIn("Độ dài: ngắn gọn", llm.calls[0][0][0]["content"])

    def test_no_learner_means_no_persona(self):
        llm = ScriptedLLM(SimpleNamespace(content="Chào bạn!", tool_calls=None))
        reply = self.client(llm).post("/respond", json=BODY).json()
        self.assertEqual(reply["persona_proposals"], [])
        self.assertNotIn("tools", llm.calls[0][1])
        self.assertNotIn("</persona>", llm.calls[0][0][0]["content"])


if __name__ == "__main__":
    unittest.main()
