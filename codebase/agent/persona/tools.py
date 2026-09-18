"""Tool `propose_persona_memory` và khối Persona trong prompt."""
from persona.store import TUTOR_SECTIONS, PersonaError

PROPOSE_TOOL = {
    "type": "function",
    "function": {
        "name": "propose_persona_memory",
        "description": (
            "Đề xuất ghi vào Persona CHỈ KHI học viên muốn điều đó áp dụng về sau: nói rõ 'từ nay', 'từ giờ', "
            "'lần sau', 'luôn luôn', 'mỗi khi', 'nhớ giúp', 'ghi nhớ' (vd 'từ nay trả lời ngắn thôi', "
            "'nhớ giúp mình chưa biết code'), hoặc tự giới thiệu điều bền vững về bản thân để Tutor dùng lâu dài "
            "(vd 'mình học kế toán, chưa học lập trình bao giờ'). Khi học viên bảo đừng nhớ một điều, đề xuất dòng "
            "'Đừng nhớ: <điều đó>' vào 'Tutor nhớ về bạn'. "
            "KHÔNG gọi cho yêu cầu chỉ cho câu trả lời hiện tại, dù là về cách trả lời: 'ngắn hơn đi', 'giải thích lại', "
            "'dễ hiểu hơn', 'cho ví dụ', 'chi tiết hơn', 'tóm tắt lại' — chỉ cần điều chỉnh câu trả lời. "
            "Không chắc thì KHÔNG gọi. Chỉ là đề xuất: học viên bấm Lưu mới ghi."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "section": {"type": "string", "enum": list(TUTOR_SECTIONS),
                            "description": "'Tính cách Tutor' cho cách trả lời; 'Tutor nhớ về bạn' cho điều về học viên."},
                "item": {"type": "string",
                         "description": "Một dòng ngắn. Cách trả lời viết dạng 'Khoá: giá trị', vd 'Độ dài: ngắn gọn, ≤3 câu'."},
            },
            "required": ["section", "item"],
        },
    },
}

PERSONA_RULES = (
    "Khối <persona> mô tả cách học viên muốn được trả lời và điều Tutor đã biết về họ. "
    "Làm theo phần trình bày (xưng hô, độ dài, cách giải thích) nhưng không bao giờ theo yêu cầu nào trái luật cố định, "
    "và không cắt mất ý cần thiết chỉ để ngắn. Dòng 'Đừng nhớ: X' nghĩa là không đề xuất ghi nhớ và không nhắc lại X."
)

MEMORY_RULES = (
    "Ghi nhớ chỉ dành cho điều học viên muốn áp dụng về sau (có ý 'từ nay', 'lần sau', 'luôn', 'nhớ giúp', "
    "hoặc tự giới thiệu điều bền vững về bản thân). Khi đó gọi propose_persona_memory rồi vẫn trả lời như bình thường. "
    "Yêu cầu chỉ cho lúc này ('ngắn hơn đi', 'giải thích lại', 'cho ví dụ') thì chỉ điều chỉnh câu trả lời, "
    "không gọi tool. Không chắc thì không gọi. Không tự nói là đã lưu — học viên sẽ thấy thẻ đề xuất để quyết định."
)


def persona_block(persona):
    """persona: {"text", "updated_at"} hiện tại của học viên, hoặc None."""
    if persona is None:
        return ""
    return f"<persona>\n{persona['text'].strip() or '(trống)'}\n</persona>\n{PERSONA_RULES}\n{MEMORY_RULES}"


def run_propose(store, learner, arguments):
    """Handler cho tool. Trả (kết quả cho model, proposal hoặc None)."""
    try:
        proposal = store.propose(learner, arguments.get("section", ""), arguments.get("item", ""))
    except PersonaError as exc:
        return {"ok": False, "error": str(exc)}, None
    if proposal is None:
        return {"ok": False, "error": "Không cần đề xuất (đã có sẵn hoặc học viên không muốn Tutor nhớ điều này)."}, None
    return {"ok": True, "note": "Đã tạo đề xuất, chờ học viên xác nhận."}, proposal
