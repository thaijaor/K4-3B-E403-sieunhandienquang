"""Persona service — TODO(Thái). Route theo bảng "Persona service" trong codebase/app/CONTRACT.md.
Học viên lấy từ header X-Learner-ID do BE gửi. Chưa làm thì trả 501."""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/persona", tags=["persona"])


def not_ready():
    raise HTTPException(501, "Persona chưa làm.")


@router.get("")
def get_persona():
    not_ready()


@router.put("")
def save_persona():
    not_ready()


@router.delete("/memory")
def clear_memory():
    not_ready()


@router.post("/undo")
def undo():
    not_ready()


@router.post("/proposals/{proposal_id}/accept")
def accept(proposal_id: str):
    not_ready()


@router.post("/proposals/{proposal_id}/reject")
def reject(proposal_id: str):
    not_ready()
