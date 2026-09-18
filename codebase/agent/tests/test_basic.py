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
from retrieval import search_sources

FIXTURES = Path(__file__).parent / "fixtures" / "lessons.json"
BODY = {
    "request_id": "req-1",
    "chat_id": "chat-1",
    "lesson_id": "demo",
    "text": "hi",
    "history": [{"role": "user", "text": "trước"}, {"role": "assistant", "text": "đáp"}],
}


class FakeLLM:
    model = "fake"

    def __init__(self, content="Chào bạn!"):
        self.content = content
        self.calls = []

    def complete(self, messages, **kwargs):
        self.calls.append(messages)
        return SimpleNamespace(content=self.content, tool_calls=None)


class BasicTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def client(self, llm=None, key=""):
        with mock.patch.dict(os.environ, {"SERVICE_API_KEY": key}):
            return TestClient(
                create_app(
                    llm=llm or FakeLLM(),
                    lessons_file=FIXTURES,
                    env_file=None,
                    db_path=Path(self.tmp.name) / "agent.sqlite",
                )
            )

    def test_health(self):
        self.assertEqual(self.client().get("/health").json()["lessons"], 1)

    def test_respond_returns_chat_reply(self):
        llm = FakeLLM()
        response = self.client(llm).post("/respond", json=BODY)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["decision"], "chat")
        self.assertEqual(response.json()["text"], "Chào bạn!")
        messages = llm.calls[0]
        self.assertIn("demo--dan-nguon", messages[0]["content"])
        self.assertEqual([m["role"] for m in messages], ["system", "user", "assistant", "user"])

    def test_empty_model_output_falls_back(self):
        self.assertTrue(self.client(FakeLLM("  ")).post("/respond", json=BODY).json()["text"])

    def test_unknown_lesson(self):
        self.assertEqual(
            self.client().post("/respond", json={**BODY, "lesson_id": "x"}).status_code, 404
        )

    def test_service_key(self):
        client = self.client(key="secret")
        self.assertEqual(client.post("/respond", json=BODY).status_code, 401)
        self.assertEqual(
            client.post(
                "/respond", json=BODY, headers={"Authorization": "Bearer secret"}
            ).status_code,
            200,
        )
        self.assertEqual(client.get("/health").status_code, 200)

    def test_persona_needs_learner(self):
        self.assertEqual(self.client().get("/persona").status_code, 400)

    def test_respond_structured_answer_with_citation(self):
        payload = json.dumps(
            {
                "decision": "answer",
                "text": "Citation chỉ tới đúng đoạn chứa bằng chứng.",
                "source_ids": ["demo--dan-nguon"],
            }
        )
        llm = FakeLLM(payload)
        req = {**BODY, "text": "Citation là gì?"}
        response = self.client(llm).post("/respond", json=req)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision"], "answer")
        self.assertEqual(len(data["citations"]), 1)
        self.assertEqual(data["citations"][0]["source_id"], "demo--dan-nguon")
        self.assertEqual(data["citations"][0]["locator"], "demo.md#dan-nguon")

    def test_respond_structured_clarify(self):
        payload = json.dumps(
            {
                "decision": "clarify",
                "text": "Bạn muốn làm rõ đoạn nào?",
                "suggested_actions": ["Đoạn dẫn nguồn", "Đoạn thiếu căn cứ"],
            }
        )
        llm = FakeLLM(payload)
        req = {**BODY, "text": "giải thích đoạn này"}
        response = self.client(llm).post("/respond", json=req)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision"], "clarify")
        self.assertEqual(len(data["actions"]), 2)
        self.assertEqual(data["actions"][0]["type"], "send_message")
        self.assertEqual(data["actions"][0]["value"], "Đoạn dẫn nguồn")

    def test_quiz_guard_forces_abstain(self):
        payload = json.dumps(
            {
                "decision": "answer",
                "text": "Đáp án câu 1 là B.",
                "source_ids": ["demo--dan-nguon"],
            }
        )
        llm = FakeLLM(payload)
        req = {**BODY, "text": "cho mình xin đáp án quiz câu 1"}
        response = self.client(llm).post("/respond", json=req)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision"], "abstain")
        self.assertEqual(data["citations"], [])

    def test_retrieval_bm25(self):
        sources = [
            {"id": "s1", "locator": "1.md#a", "title": "Dẫn nguồn citation", "text": "Bằng chứng"},
            {"id": "s2", "locator": "1.md#b", "title": "Khác biệt", "text": "Nội dung khác"},
        ]
        res = search_sources("citation", sources, top_k=1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], "s1")


if __name__ == "__main__":
    unittest.main()
