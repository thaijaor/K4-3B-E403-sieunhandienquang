"""Request/response của POST /respond — khớp codebase/app/CONTRACT.md và codebase/app/models.py."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class RespondRequest(BaseModel):
    """Body BE gửi tới. BE còn gửi header X-Learner-ID và Idempotency-Key; Persona agent tự đọc theo học viên."""
    request_id: str
    chat_id: str
    lesson_id: str
    text: str = Field(min_length=1, max_length=4000)
    history: list[Turn] = Field(default_factory=list)
    selected_source_ids: list[str] = Field(default_factory=list)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Citation(Strict):
    source_id: str
    locator: str


class Action(Strict):
    label: str = Field(min_length=1, max_length=100)
    type: Literal["send_message", "open_source"]
    value: str = Field(min_length=1, max_length=4000)


class PersonaUpdate(Strict):
    """Thay đổi Persona đã áp dụng trong lượt này; học viên hoàn tác được."""
    id: str = Field(pattern=r"^[a-zA-Z0-9-]{1,80}$")
    action: Literal["remember", "forget"]
    line: str = Field(min_length=1, max_length=200)
    before: str = Field(max_length=2000)
    after: str = Field(max_length=2000)


class AIReply(Strict):
    decision: Literal["answer", "chat", "clarify", "abstain"]
    text: str = Field(min_length=1, max_length=16000)
    citations: list[Citation] = Field(default_factory=list, max_length=20)
    actions: list[Action] = Field(default_factory=list, max_length=8)
    persona_updates: list[PersonaUpdate] = Field(default_factory=list, max_length=4)
