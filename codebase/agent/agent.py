"""Xử lý một lượt /respond cho Agent Service.

Kết hợp retrieval BM25, quyết định có citation, guard quiz và tool đề xuất Persona.
"""
import json
import logging
import re
import time
from pathlib import Path

from persona.tools import PROPOSE_TOOL, run_propose
from prompt import build_messages
from retrieval import search_sources
from schemas import Action, AIReply, Citation, RespondRequest

LOG = logging.getLogger("agent")
FALLBACK = "Mình chưa trả lời được lúc này, bạn thử hỏi lại nhé."
MAX_ROUNDS = 3
TRACE_FILE = Path(__file__).resolve().parent.parent.parent / "eval" / "trace.jsonl"

QUIZ_PATTERN = re.compile(
    r"\b(đáp án|giải bài tập|bài tập trắc nghiệm|chọn câu|câu \d+ chọn)\b", re.IGNORECASE
)


def _assistant_message(message):
    """Giữ nguyên message/tool call của provider khi đưa lại vào vòng hội thoại."""
    if hasattr(message, "model_dump"):
        return message.model_dump(exclude_none=True)
    return {
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in (getattr(message, "tool_calls", None) or [])
        ],
    }


def _clean_json_text(raw: str) -> str:
    """Loại bỏ markdown code blocks nếu model bọc JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _parse_llm_response(raw_text: str) -> dict:
    """Parse JSON phản hồi từ LLM, fallback linh hoạt nếu model trả text thường."""
    cleaned = _clean_json_text(raw_text)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    lower = raw_text.lower()
    if any(greet in lower for greet in ["chào", "hi ", "hello", "cảm ơn", "tạm biệt"]):
        return {"decision": "chat", "text": raw_text, "source_ids": []}
    return {"decision": "answer", "text": raw_text, "source_ids": []}


def _record_trace(request: RespondRequest, reply: AIReply, duration_ms: float):
    """Ghi vết lượt gọi vào eval/trace.jsonl phục vụ kiểm thử và đo CP3."""
    try:
        TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "timestamp": time.time(),
            "request_id": request.request_id,
            "chat_id": request.chat_id,
            "lesson_id": request.lesson_id,
            "question": request.text,
            "decision": reply.decision,
            "citations": [citation.source_id for citation in reply.citations],
            "text": reply.text,
            "duration_ms": round(duration_ms, 1),
        }
        with open(TRACE_FILE, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        LOG.warning("Không thể ghi trace log vào %s", TRACE_FILE, exc_info=True)


def respond(
    request: RespondRequest,
    lesson: dict,
    llm,
    learner: str = "",
    persona_store=None,
) -> AIReply:
    start_time = time.monotonic()
    all_sources = lesson.get("sources", [])
    sources_map = {source["id"]: source for source in all_sources}
    relevant_sources = search_sources(
        request.text, all_sources, selected_ids=request.selected_source_ids, top_k=3
    )

    persona = persona_store.get(learner) if persona_store is not None and learner else None
    messages = build_messages(
        request,
        lesson,
        relevant_sources=relevant_sources,
        persona=persona,
    )
    proposals = []
    tools = {}

    if persona is not None:
        def propose(arguments):
            result, proposal = run_propose(persona_store, learner, arguments)
            if proposal:
                proposals.append(proposal)
            return result

        tools["propose_persona_memory"] = (PROPOSE_TOOL, propose)

    message = None
    for _ in range(MAX_ROUNDS):
        options = {"temperature": 0.2}
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
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
        tools.pop("propose_persona_memory", None)

    raw_content = (
        (message.content or "").strip()
        if message is not None and not (getattr(message, "tool_calls", None) or [])
        else ""
    )
    parsed = _parse_llm_response(raw_content)
    raw_decision = str(parsed.get("decision", "chat")).lower()
    text = (parsed.get("text") or "").strip() or FALLBACK
    text = text[:16000]
    proposed_source_ids = parsed.get("source_ids") or []
    if isinstance(proposed_source_ids, str):
        proposed_source_ids = [proposed_source_ids]
    suggested_actions = parsed.get("suggested_actions") or []

    if QUIZ_PATTERN.search(request.text):
        decision = "abstain"
        text = (
            "Trợ giảng không thể cung cấp trực tiếp đáp án quiz hoặc bài kiểm tra. "
            "Bạn hãy xem lại nội dung bài học để tự làm nhé."
        )
        citations = []
    elif raw_decision not in ("answer", "chat", "clarify", "abstain"):
        decision = "chat"
        citations = []
    else:
        decision = raw_decision
        citations = []

    if decision == "answer":
        valid_citations = [
            Citation(source_id=source_id, locator=sources_map[source_id]["locator"])
            for source_id in proposed_source_ids
            if source_id in sources_map
        ]
        if not valid_citations and relevant_sources:
            top_source = relevant_sources[0]
            valid_citations.append(
                Citation(source_id=top_source["id"], locator=top_source["locator"])
            )
        if not valid_citations:
            decision = "abstain"
            text = (
                "Nội dung bài học hiện tại chưa có thông tin chính xác về câu hỏi này. "
                "Bạn hãy thử tham khảo các mục khác trong bài nhé."
            )
            citations = []
        else:
            citations = valid_citations[:5]

    actions = []
    if decision in ("clarify", "abstain") and suggested_actions:
        for action in suggested_actions[:3]:
            if isinstance(action, str) and action.strip():
                clean_action = action.strip()
                actions.append(
                    Action(
                        label=clean_action[:100],
                        type="send_message",
                        value=clean_action[:4000],
                    )
                )

    reply = AIReply(
        decision=decision,
        text=text,
        citations=citations,
        actions=actions,
        persona_proposals=proposals[:4],
    )
    _record_trace(request, reply, (time.monotonic() - start_time) * 1000)
    return reply
