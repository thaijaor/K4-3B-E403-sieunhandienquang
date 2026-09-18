"""Test-only upstream doubles. Never imported by the application server."""
import copy
import threading
import uuid
from lessons import load_lessons
from pathlib import Path
from fastapi import HTTPException


class FakeServices:
    ai_url = "test-double"
    persona_url = "test-double"
    is_fixture = True

    def __init__(self):
        self.lessons = {x["id"]: x for x in load_lessons(Path(__file__).parents[1] / "lessons.sample.json")}
        self.calls = []
        self.personas = {}
        self.proposals = {}
        self.failure = None
        self.reply_override = None
        self.entered = threading.Event()
        self.release = None

    def current(self, owner):
        if owner not in self.personas:
            self.personas[owner] = {"text": "# PERSONA — Tutor của tôi\n\n## Tính cách Tutor\n- Xưng hô: mình – bạn\n\n## Tutor nhớ về bạn\n\n## Không được nhớ\n", "updated_at": "Fixture UI"}
        return self.personas[owner]

    def request(self, kind, method, path, owner, payload=None, request_id=None):
        self.calls.append((kind, method, path, owner, copy.deepcopy(payload), request_id))
        if self.failure:
            raise self.failure
        if kind == "ai":
            self.entered.set()
            if self.release:
                self.release.wait(5)
            if self.reply_override is not None:
                return copy.deepcopy(self.reply_override)
            text = payload["text"].lower()
            source = self.lessons[payload["lesson_id"]]["sources"][0]
            result = {"decision": "answer", "text": "[Fixture UI] Citation giúp bạn mở đúng nguồn để đối chiếu phát biểu. Đây là phản hồi cố định để thử giao diện, không phải AI.", "citations": [{"source_id": source["id"], "locator": source["locator"]}], "actions": [], "persona_proposals": []}
            if "mơ hồ" in text or "giải thích đoạn" in text:
                result.update(decision="clarify", text="[Fixture UI] Bạn muốn làm rõ phần dẫn nguồn hay phần thiếu căn cứ?", citations=[], actions=[{"type": "send_message", "label": "Phần dẫn nguồn", "value": "Citation là gì?"}])
            if "quiz" in text or "ngoài bài" in text:
                result.update(decision="abstain", text="[Fixture UI] Mình chưa thể trả lời yêu cầu này. Bạn có thể xem lại bài mẫu.", citations=[])
            if "ghi nhớ" in text:
                current = self.current(owner)
                before = current["text"]
                if "## Tutor nhớ về bạn\n" not in before:
                    before += "\n\n## Tutor nhớ về bạn\n"
                proposal = {"id": str(uuid.uuid4()), "before": current["text"], "after": before.replace("## Tutor nhớ về bạn\n", "## Tutor nhớ về bạn\n- Ưu tiên ví dụ dễ hiểu (fixture)\n", 1)}
                self.proposals[proposal["id"]] = (owner, proposal)
                result["persona_proposals"] = [proposal]
            return result
        current = self.current(owner)
        if method == "GET":
            return copy.deepcopy(current)
        if path.endswith("/reject"):
            return {"status": "rejected"}
        if path.endswith("/accept"):
            proposal_owner, proposal = self.proposals[path.split("/")[-2]]
            if owner != proposal_owner:
                raise HTTPException(404, "Proposal not found")
            text = payload.get("edited_text") if payload.get("edited_text") is not None else proposal["after"]
        elif path.endswith("/memory"):
            text = "# PERSONA — Tutor của tôi\n\n## Tính cách Tutor\n- Xưng hô: mình – bạn\n\n## Tutor nhớ về bạn\n\n## Không được nhớ\n"
        else:
            text = payload["text"]
        self.personas[owner] = {"text": text, "updated_at": "Fixture UI"}
        return copy.deepcopy(self.personas[owner])
