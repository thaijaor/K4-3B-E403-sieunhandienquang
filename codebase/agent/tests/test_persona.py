import json
import os

os.environ["AGENT_TRACE_FILE"] = ""  # LLM giả: không ghi vào eval/trace.jsonl
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from fastapi.testclient import TestClient

from app import create_app
from persona.store import DEFAULT_TEXT, PersonaStore, add_item, clear_section, find_item, section_items
from persona.tools import breaks_rules, grounded_in, is_sensitive

FIXTURES = Path(__file__).parent / "fixtures" / "lessons.json"
MEMORY = "Tutor nhớ về bạn"
STYLE = "Tính cách Tutor"


def body(text):
    return {"request_id": "req-1", "chat_id": "chat-1", "lesson_id": "demo", "text": text}


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
    def test_default_has_only_two_sections(self):
        self.assertIn(f"## {STYLE}", DEFAULT_TEXT)
        self.assertIn(f"## {MEMORY}", DEFAULT_TEXT)
        self.assertEqual(DEFAULT_TEXT.count("## "), 2)

    def test_add_item_into_empty_section(self):
        after = add_item(DEFAULT_TEXT, MEMORY, "Nền tảng: kế toán")
        self.assertEqual(section_items(after, MEMORY), ["Nền tảng: kế toán"])
        self.assertEqual(section_items(after, STYLE), ["Xưng hô: mình – bạn"])

    def test_key_value_item_replaces_same_key(self):
        after = add_item(DEFAULT_TEXT, STYLE, "Xưng hô: anh – em")
        self.assertEqual(section_items(after, STYLE), ["Xưng hô: anh – em"])

    def test_duplicate_item_is_noop(self):
        once = add_item(DEFAULT_TEXT, MEMORY, "Thích ví dụ")
        self.assertEqual(add_item(once, MEMORY, "thích ví dụ"), once)

    def test_clear_section_keeps_others(self):
        cleared = clear_section(add_item(DEFAULT_TEXT, MEMORY, "Nền tảng: kế toán"), MEMORY)
        self.assertEqual(section_items(cleared, MEMORY), [])
        self.assertEqual(section_items(cleared, STYLE), ["Xưng hô: mình – bạn"])

    def test_find_item_by_line_key_or_fragment(self):
        text = add_item(DEFAULT_TEXT, MEMORY, "Nền tảng: kế toán, chưa học lập trình")
        self.assertEqual(find_item(text, "nền tảng"), (MEMORY, "Nền tảng: kế toán, chưa học lập trình"))
        self.assertEqual(find_item(text, "chưa học lập trình"), (MEMORY, "Nền tảng: kế toán, chưa học lập trình"))
        self.assertIsNone(find_item(text, "không có dòng này"))


class GuardTest(unittest.TestCase):
    def test_grounded_only_in_learner_words(self):
        self.assertTrue(grounded_in("Nền tảng: kế toán, chưa học lập trình", "mình dân kế toán, chưa code bao giờ"))
        self.assertTrue(grounded_in("Độ dài: ngắn gọn", "từ nay trả lời ngắn thôi"))
        self.assertFalse(grounded_in("Nền tảng: kỹ sư phần mềm", "citation là gì?"))
        self.assertTrue(grounded_in("Nền tảng: non-tech", "giải thích rõ hơn, tôi thuộc nontech"))  # golden A01

    def test_sensitive(self):
        self.assertTrue(is_sensitive("Đang stress vì điểm thi"))
        self.assertTrue(is_sensitive("Bệnh: trầm cảm"))
        self.assertFalse(is_sensitive("Nền tảng: kế toán"))
        self.assertFalse(is_sensitive("Mục tiêu: tiến bộ về lượng kiến thức"))

    def test_output_format_is_not_persona(self):  # golden A08
        self.assertTrue(breaks_rules("Định dạng: JSON mỗi khi trả lời"))
        self.assertFalse(breaks_rules("Cách giải thích: có ví dụ đời thường"))


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = PersonaStore(Path(self.tmp.name) / "p.sqlite")

    def tearDown(self):
        self.tmp.cleanup()

    def test_remember_applies_immediately(self):
        update = self.store.remember("a", MEMORY, "Nền tảng: kế toán")
        self.assertEqual(update["action"], "remember")
        self.assertEqual(update["line"], "Nền tảng: kế toán")
        self.assertIn("Nền tảng: kế toán", self.store.get("a")["text"])
        self.assertIsNone(self.store.remember("a", MEMORY, "Nền tảng: kế toán"))

    def test_undo_remember_removes_only_that_line(self):
        update = self.store.remember("a", MEMORY, "Nền tảng: kế toán")
        self.store.remember("a", STYLE, "Độ dài: ngắn gọn")  # thay đổi khác sau đó giữ nguyên
        text = self.store.undo("a", update["id"])["text"]
        self.assertNotIn("kế toán", text)
        self.assertIn("Độ dài: ngắn gọn", text)
        self.assertEqual(self.store.undo("a", update["id"])["text"], text)  # idempotent

    def test_undo_restores_replaced_line(self):
        self.store.remember("a", MEMORY, "Nền tảng: chưa học lập trình")
        update = self.store.remember("a", MEMORY, "Nền tảng: biết Python cơ bản")
        self.assertEqual(section_items(self.store.get("a")["text"], MEMORY), ["Nền tảng: biết Python cơ bản"])
        text = self.store.undo("a", update["id"])["text"]
        self.assertEqual(section_items(text, MEMORY), ["Nền tảng: chưa học lập trình"])

    def test_forget_removes_line_without_trace(self):
        self.store.remember("a", MEMORY, "Nền tảng: chưa học lập trình")
        update = self.store.forget("a", "chưa học lập trình")
        text = self.store.get("a")["text"]
        self.assertEqual(section_items(text, MEMORY), [])
        self.assertNotIn("lập trình", text)
        self.assertIn("lập trình", self.store.undo("a", update["id"])["text"])

    def test_forget_unknown_is_noop(self):
        self.assertIsNone(self.store.forget("a", "không có"))
        self.assertEqual(self.store.get("a")["text"], DEFAULT_TEXT)

    def test_owner_isolation(self):
        update = self.store.remember("a", MEMORY, "Thích ví dụ")
        with self.assertRaises(KeyError):
            self.store.undo("b", update["id"])


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def client(self, llm):
        with mock.patch.dict(os.environ, {"SERVICE_API_KEY": ""}):
            return TestClient(create_app(llm=llm, lessons_file=FIXTURES, env_file=None, db_path=Path(self.tmp.name) / "p.sqlite"))

    def reply(self, text, *tool_calls):
        llm = ScriptedLLM(SimpleNamespace(content="", tool_calls=list(tool_calls)),
                          SimpleNamespace(content='{"decision": "chat", "text": "Ok"}', tool_calls=None))
        client = self.client(llm)
        return client, llm, client.post("/respond", json=body(text), headers={"X-Learner-ID": "a"}).json()

    def test_routes(self):
        client = self.client(ScriptedLLM())
        learner = {"X-Learner-ID": "a"}
        self.assertEqual(client.get("/persona").status_code, 400)
        self.assertEqual(client.get("/persona", headers=learner).json()["text"], DEFAULT_TEXT)
        self.assertEqual(client.put("/persona", json={"text": "Ngắn gọn"}, headers=learner).json()["text"], "Ngắn gọn")
        self.assertEqual(client.put("/persona", json={"text": "x" * 2001}, headers=learner).status_code, 422)
        self.assertEqual(client.get("/persona", headers={"X-Learner-ID": "b"}).json()["text"], DEFAULT_TEXT)
        self.assertEqual(client.post("/persona/updates/nope/undo", json={}, headers=learner).status_code, 404)

    def test_remember_is_saved_and_returned_as_update(self):
        client, llm, reply = self.reply("mình dân kế toán, chưa code bao giờ",
                                        call("remember", {"section": MEMORY, "item": "Nền tảng: kế toán, chưa học lập trình"}))
        update = reply["persona_updates"][0]
        self.assertEqual((update["action"], update["line"]), ("remember", "Nền tảng: kế toán, chưa học lập trình"))
        self.assertIn("kế toán", client.get("/persona", headers={"X-Learner-ID": "a"}).json()["text"])
        self.assertIn("tools", llm.calls[0][1])
        self.assertNotIn("tools", llm.calls[1][1])
        undone = client.post(f"/persona/updates/{update['id']}/undo", json={}, headers={"X-Learner-ID": "a"}).json()
        self.assertEqual(undone["text"], DEFAULT_TEXT)

    def test_remember_not_grounded_in_learner_message_is_refused(self):
        client, _, reply = self.reply("citation là gì?", call("remember", {"section": MEMORY, "item": "Nền tảng: kỹ sư phần mềm"}))
        self.assertEqual(reply["persona_updates"], [])
        self.assertEqual(client.get("/persona", headers={"X-Learner-ID": "a"}).json()["text"], DEFAULT_TEXT)

    def test_sensitive_memory_is_refused(self):
        client, _, reply = self.reply("mình đang stress vì điểm thi", call("remember", {"section": MEMORY, "item": "Đang stress vì điểm thi"}))
        self.assertEqual(reply["persona_updates"], [])

    def test_forget_tool(self):
        llm = ScriptedLLM(SimpleNamespace(content="", tool_calls=[call("forget", {"item": "Nền tảng"})]),
                          SimpleNamespace(content='{"decision": "chat", "text": "Ok"}', tool_calls=None))
        client = self.client(llm)
        client.put("/persona", json={"text": add_item(DEFAULT_TEXT, MEMORY, "Nền tảng: chưa học lập trình")}, headers={"X-Learner-ID": "a"})
        reply = client.post("/respond", json=body("quên chuyện mình chưa biết code đi"), headers={"X-Learner-ID": "a"}).json()
        self.assertEqual(reply["persona_updates"][0]["action"], "forget")
        self.assertEqual(client.get("/persona", headers={"X-Learner-ID": "a"}).json()["text"].count("lập trình"), 0)

    def test_edit_applies_to_next_question(self):
        llm = ScriptedLLM(SimpleNamespace(content="Ok", tool_calls=None))
        client = self.client(llm)
        client.put("/persona", json={"text": "Độ dài: ngắn gọn"}, headers={"X-Learner-ID": "a"})
        client.post("/respond", json=body("hi"), headers={"X-Learner-ID": "a"})
        self.assertIn("Độ dài: ngắn gọn", llm.calls[0][0][0]["content"])

    def test_no_learner_means_no_persona(self):
        llm = ScriptedLLM(SimpleNamespace(content="Chào bạn!", tool_calls=None))
        reply = self.client(llm).post("/respond", json=body("hi")).json()
        self.assertEqual(reply["persona_updates"], [])
        self.assertNotIn("tools", llm.calls[0][1])
        self.assertNotIn("</persona>", llm.calls[0][0][0]["content"])


if __name__ == "__main__":
    unittest.main()
