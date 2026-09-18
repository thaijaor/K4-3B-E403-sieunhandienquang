"""Route Persona mà BE proxy tới (bảng "Persona service" trong codebase/app/CONTRACT.md).
Học viên lấy từ header X-Learner-ID do BE gửi; browser không gọi thẳng service này."""
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from persona.store import MAX_CHARS, PersonaError

router = APIRouter(prefix="/persona", tags=["persona"])


class PersonaWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=MAX_CHARS)


def _store(request: Request):
    return request.app.state.persona_store


def _learner(value):
    if not value:
        raise HTTPException(400, "Thiếu X-Learner-ID.")
    return value


@router.get("")
def get_persona(request: Request, x_learner_id: str = Header("")):
    return _store(request).get(_learner(x_learner_id))


@router.put("")
def save_persona(body: PersonaWrite, request: Request, x_learner_id: str = Header("")):
    return _store(request).save(_learner(x_learner_id), body.text)


@router.delete("/memory")
def clear_memory(request: Request, x_learner_id: str = Header("")):
    return _store(request).clear_memory(_learner(x_learner_id))


@router.post("/updates/{update_id}/undo")
def undo(update_id: str, request: Request, x_learner_id: str = Header("")):
    try:
        return _store(request).undo(_learner(x_learner_id), update_id)
    except KeyError:
        raise HTTPException(404, "Không tìm thấy thay đổi.")
    except PersonaError as exc:
        raise HTTPException(422, str(exc))
