"""Xử lý một lượt /respond.

Hiện tại: vòng tool tối đa MAX_ROUNDS với tool Persona `propose_persona_memory`, kết thúc bằng trả lời dạng `chat`.
TODO(Tùng): thêm search_lesson + answer/chat/clarify/abstain vào `tools`, guard citation (README § Flow một lượt).
"""
import json

from persona.tools import PROPOSE_TOOL, run_propose
from prompt import build_messages
from schemas import AIReply

FALLBACK = "Mình chưa trả lời được lúc này, bạn thử hỏi lại nhé."
MAX_ROUNDS = 3


def _assistant_message(message):
    # Giữ nguyên message của model (kể cả trường riêng của provider, vd thought signature của Gemini).
    if hasattr(message, "model_dump"):
        return message.model_dump(exclude_none=True)
    return {"role": "assistant", "content": message.content or "", "tool_calls": [
        {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
        for c in message.tool_calls]}


def respond(request, lesson, llm, learner="", persona_store=None):
    # Persona hiện tại của học viên, đọc mỗi lượt: sửa Persona áp dụng ngay câu hỏi tiếp theo.
    persona = persona_store.get(learner) if persona_store is not None and learner else None
    messages = build_messages(request, lesson, persona)
    proposals = []
    tools = {}  # tên → (schema, handler(args) -> dict trả cho model)

    if persona is not None:
        def propose(arguments):
            result, proposal = run_propose(persona_store, learner, arguments)
            if proposal:
                proposals.append(proposal)
            return result
        tools["propose_persona_memory"] = (PROPOSE_TOOL, propose)

    message = None
    for _ in range(MAX_ROUNDS):
        options = {"temperature": 0.3}
        if tools:
            options["tools"] = [schema for schema, _ in tools.values()]
        message = llm.complete(messages, **options)
        calls = getattr(message, "tool_calls", None) or []
        if not calls:
            break
        messages.append(_assistant_message(message))
        for call in calls:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except ValueError:
                arguments = {}
            entry = tools.get(call.function.name)
            result = entry[1](arguments) if entry else {"ok": False, "error": "Tool không tồn tại."}
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False)})
        tools.pop("propose_persona_memory", None)  # mỗi lượt đề xuất tối đa một lần

    text = (message.content or "").strip()[:16000] if message and not getattr(message, "tool_calls", None) else ""
    return AIReply(decision="chat", text=text or FALLBACK, persona_proposals=proposals[:4])
