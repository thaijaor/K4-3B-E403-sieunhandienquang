"""Shared application contracts; no model prompting or Persona business logic."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NewChat(Contract):
    lesson_id: str = Field(min_length=1, max_length=100)
    without_persona: bool = False


class Question(Contract):
    text: str = Field(min_length=1, max_length=4000)
    client_request_id: str = Field(pattern=r"^[a-zA-Z0-9-]{8,80}$")
    selected_source_ids: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("text")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("Question must not be blank")
        return value.strip()


class Persona(Contract):
    text: str = Field(max_length=2000)
    version: int = Field(ge=0)
    updated_at: str


class PersonaWrite(Contract):
    text: str = Field(max_length=2000)
    expected_version: int = Field(ge=0)


class Version(Contract):
    expected_version: int = Field(ge=0)


class Accept(Version):
    edited_text: str | None = Field(default=None, max_length=2000)


class Undo(Version):
    target_version: int = Field(ge=0)


class Citation(Contract):
    source_id: str
    locator: str


class Action(Contract):
    label: str = Field(min_length=1, max_length=100)
    type: Literal["send_message", "open_source"]
    value: str = Field(min_length=1, max_length=4000)


class Proposal(Contract):
    id: str = Field(pattern=r"^[a-zA-Z0-9-]{1,80}$")
    base_version: int = Field(ge=0)
    before: str = Field(max_length=2000)
    after: str = Field(max_length=2000)


class AIReply(Contract):
    decision: Literal["answer", "chat", "clarify", "abstain"]
    text: str = Field(min_length=1, max_length=16000)
    citations: list[Citation] = Field(default_factory=list, max_length=20)
    actions: list[Action] = Field(default_factory=list, max_length=8)
    persona_proposals: list[Proposal] = Field(default_factory=list, max_length=4)
