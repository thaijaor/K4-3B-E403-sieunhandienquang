import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from fastapi.testclient import TestClient

from app import create_app

FIXTURES = Path(__file__).parent / "fixtures" / "lessons.json"
BODY = {"request_id": "req-1", "chat_id": "chat-1", "lesson_id": "demo", "text": "hi",
        "history": [{"role": "user", "text": "trước"}, {"role": "assistant", "text": "đáp"}]}


class FakeLLM:
    model = "fake"

    def __init__(self, content="Chào bạn!"):
        self.content = content
        self.calls = []

    def complete(self, messages, **kwargs):
        self.calls.append(messages)
        return SimpleNamespace(content=self.content, tool_calls=None)


class BasicTest(unittest.TestCase):
    def client(self, llm=None, key=""):
        with mock.patch.dict(os.environ, {"SERVICE_API_KEY": key}):
            return TestClient(create_app(llm=llm or FakeLLM(), lessons_file=FIXTURES, env_file=None))

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
        self.assertEqual(self.client().post("/respond", json={**BODY, "lesson_id": "x"}).status_code, 404)

    def test_service_key(self):
        client = self.client(key="secret")
        self.assertEqual(client.post("/respond", json=BODY).status_code, 401)
        self.assertEqual(client.post("/respond", json=BODY, headers={"Authorization": "Bearer secret"}).status_code, 200)
        self.assertEqual(client.get("/health").status_code, 200)

    def test_persona_not_ready(self):
        self.assertEqual(self.client().get("/persona").status_code, 501)


if __name__ == "__main__":
    unittest.main()
