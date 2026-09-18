"""Xử lý một lượt /respond cho Agent Service.

Thực hiện:
1. Retrieval các đoạn nguồn (sources) bằng BM25 từ bài học đang mở.
2. Ghép prompt và gọi LLM ra quyết định JSON (answer, chat, clarify, abstain).
3. Code guard: kiểm tra và điền locator chuẩn cho citation, hạ xuống abstain nếu thiếu căn cứ.
4. Ghi log trace JSONL vào eval/trace.jsonl phục vụ kiểm thử và đo số liệu CP3.
"""
import json
import logging
import re
import time
from pathlib import Path

from prompt import build_messages
from retrieval import search_sources
from schemas import Action, AIReply, Citation, RespondRequest

LOG = logging.getLogger("agent")
FALLBACK = "Mình chưa trả lời được lúc này, bạn thử hỏi lại nhé."
TRACE_FILE = Path(__file__).resolve().parent.parent.parent / "eval" / "trace.jsonl"

QUIZ_PATTERN = re.compile(
    r"\b(đáp án|giải bài tập|bài tập trắc nghiệm|chọn câu|câu \d+ chọn)\b", re.IGNORECASE
)


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

    # Nếu model trả về chuỗi có chứa JSON bên trong
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # Fallback cho trường hợp trả về text thường
    lower = raw_text.lower()
    if any(greet in lower for greet in ["chào", "hi ", "hello", "cảm ơn", "tạm biệt"]):
        return {"decision": "chat", "text": raw_text, "source_ids": []}
    return {"decision": "answer", "text": raw_text, "source_ids": []}


def _record_trace(request: RespondRequest, reply: AIReply, duration_ms: float):
    """Ghi lại vết lượt gọi vào eval/trace.jsonl cho Cường & đo số liệu CP3."""
    try:
        TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "timestamp": time.time(),
            "request_id": request.request_id,
            "chat_id": request.chat_id,
            "lesson_id": request.lesson_id,
            "question": request.text,
            "decision": reply.decision,
            "citations": [c.source_id for c in reply.citations],
            "text": reply.text,
            "duration_ms": round(duration_ms, 1),
        }
        with open(TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        LOG.warning("Không thể ghi trace log vào %s", TRACE_FILE, exc_info=True)


def respond(request: RespondRequest, lesson: dict, llm) -> AIReply:
    start_time = time.monotonic()
    all_sources = lesson.get("sources", [])
    sources_map = {s["id"]: s for s in all_sources}

    # 1. Retrieval: tìm top-3 đoạn nguồn liên quan
    relevant_sources = search_sources(
        request.text, all_sources, selected_ids=request.selected_source_ids, top_k=3
    )

    # 2. Xây dựng messages và gọi LLM
    messages = build_messages(request, lesson, relevant_sources=relevant_sources)
    llm_output = llm.complete(messages, temperature=0.2)
    raw_content = (llm_output.content or "").strip()

    # 3. Parse kết quả từ LLM
    parsed = _parse_llm_response(raw_content)
    raw_decision = str(parsed.get("decision", "chat")).lower()
    text = (parsed.get("text") or "").strip() or FALLBACK
    text = text[:16000]
    proposed_source_ids = parsed.get("source_ids") or []
    if isinstance(proposed_source_ids, str):
        proposed_source_ids = [proposed_source_ids]
    suggested_actions = parsed.get("suggested_actions") or []

    # 4. Code Guardrails
    # 4.1. Chặn hỏi đáp án quiz/bài tập
    if QUIZ_PATTERN.search(request.text):
        decision = "abstain"
        text = "Trợ giảng không thể cung cấp trực tiếp đáp án quiz hoặc bài kiểm tra. Bạn hãy xem lại nội dung bài học để tự làm nhé."
        citations = []
    # 4.2. Kiểm tra quyết định hợp lệ
    elif raw_decision not in ("answer", "chat", "clarify", "abstain"):
        decision = "chat"
        citations = []
    else:
        decision = raw_decision
        citations = []

    # 4.3. Xử lý Citations cho answer
    if decision == "answer":
        valid_citations = []
        for s_id in proposed_source_ids:
            if s_id in sources_map:
                locator = sources_map[s_id]["locator"]
                valid_citations.append(Citation(source_id=s_id, locator=locator))

        # Nếu model không trả source_id hợp lệ, nhưng ta có relevant_sources khớp tốt
        if not valid_citations and relevant_sources:
            # Lấy nguồn top-1 tìm được
            top_source = relevant_sources[0]
            valid_citations.append(
                Citation(source_id=top_source["id"], locator=top_source["locator"])
            )

        # Nếu vẫn không có citation hợp lệ -> Bắt buộc hạ xuống abstain theo CONTRACT
        if not valid_citations:
            decision = "abstain"
            text = "Nội dung bài học hiện tại chưa có thông tin chính xác về câu hỏi này. Bạn hãy thử tham khảo các mục khác trong bài nhé."
            citations = []
        else:
            citations = valid_citations[:5]

    # 4.4. Xây dựng Actions (cho clarify hoặc gợi ý)
    actions = []
    if decision in ("clarify", "abstain") and suggested_actions:
        for act in suggested_actions[:3]:
            if isinstance(act, str) and act.strip():
                clean_act = act.strip()
                actions.append(
                    Action(label=clean_act[:100], type="send_message", value=clean_act[:4000])
                )

    # 4.5. Persona Proposals: luôn để rỗng khi persona service chưa chạy
    reply = AIReply(
        decision=decision,
        text=text,
        citations=citations,
        actions=actions,
        persona_proposals=[],
    )

    # 5. Ghi trace log cho CP3
    duration_ms = (time.monotonic() - start_time) * 1000
    _record_trace(request, reply, duration_ms)

    return reply
