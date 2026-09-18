"""Xử lý một lượt /respond.

Skeleton: gọi LLM một lần, trả lời dạng `chat` (không citation).
TODO(Tùng): thay bằng vòng tool theo README § Flow một lượt — search_lesson, answer/chat/clarify/abstain, guard.
"""
from prompt import build_messages
from schemas import AIReply

FALLBACK = "Mình chưa trả lời được lúc này, bạn thử hỏi lại nhé."


def respond(request, lesson, llm):
    message = llm.complete(build_messages(request, lesson), temperature=0.3)
    text = (message.content or "").strip()[:16000] or FALLBACK
    return AIReply(decision="chat", text=text)
