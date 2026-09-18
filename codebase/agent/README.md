# Agent service — VLearn Tutor

Service AI riêng mà backend (`codebase/app`) gọi qua `POST /respond`. Service này cũng chứa luôn Persona.

**Hiện trạng:** gọi được model thật với system prompt cơ bản; Persona đã xong (store, route, đưa vào prompt, tool đề xuất ghi nhớ). Mọi câu vẫn trả `decision: "chat"` — chưa đọc nội dung bài, chưa citation/clarify (phần của Tùng).

> Thiết kế và tool dưới đây là **đề xuất**. Người làm tự xem xét, đổi tên, gộp, tách hoặc viết lại nếu thấy hợp lý hơn — chỉ cần giữ đúng contract với backend (`codebase/app/CONTRACT.md`) và cập nhật lại README này.

## Chạy

Từ thư mục gốc repo (dùng chung `.venv` với app):

```powershell
.\.venv\Scripts\python.exe -m pip install -r codebase/agent/requirements.txt
copy codebase\agent\.env.example codebase\agent\.env   # điền OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL
.\.venv\Scripts\python.exe -m uvicorn app:create_app --factory --app-dir codebase/agent --host 127.0.0.1 --port 8001
```

Nối backend: chạy app với `AI_API_URL=http://127.0.0.1:8001` và `PERSONA_API_URL=http://127.0.0.1:8001`.

Test: `cd codebase/agent` rồi `..\..\.venv\Scripts\python.exe -m unittest discover -s tests -v` (dùng LLM giả, không tốn key).

## Cấu trúc

| File | Vai trò | Người |
|---|---|---|
| `app.py` | FastAPI: `/health`, `/respond`, kiểm tra service key, map lỗi model → 502/504 | chung |
| `schemas.py` | Request/response theo CONTRACT | chung |
| `llm.py` | Client `openai` (Gemini qua endpoint tương thích OpenAI); `complete()` nhận thêm `tools`, `tool_choice`… | chung |
| `lessons.py` | Đọc manifest; mỗi H2 `## Tên {#anchor}` là một đoạn nguồn. Giữ khớp `codebase/app/lessons.py` | chung |
| `prompt.py` | System prompt cơ bản + ghép messages | Tùng (flow), Thái (`persona_block`) |
| `agent.py` | Xử lý một lượt — hiện gọi LLM 1 lần | Tùng |
| `persona/` | Store SQLite, 5 route Persona, tool `propose_persona_memory`, khối `<persona>` trong prompt | Thái |
| `tests/` | Test với LLM giả + bài fixture | ai sửa phần nào thêm test phần đó |

## Thiết kế

### Vị trí trong hệ thống

```
FE ──▶ BE (codebase/app) ──POST /respond──────────▶ AGENT ──▶ LLM (Gemini)
                        ──/persona/* (proxy)──────▶   │
                                                      └─ Persona store (SQLite)
```

BE gửi kèm header `X-Learner-ID` (học viên), `Idempotency-Key` và `Authorization: Bearer <SERVICE_API_KEY>`. Học viên và bài luôn do server xác định, model không tự chọn được.

### Bốn kiểu kết thúc một lượt

| `decision` | Khi nào | Citation | Ví dụ |
|---|---|---|---|
| `answer` | Trả lời nội dung bài, có căn cứ | **Bắt buộc ≥1** | "Citation là gì?" |
| `chat` | Chào hỏi, cảm ơn, câu không liên quan bài — trả lời thường | Không cần | "hi", "cảm ơn nha" |
| `clarify` | Không rõ học viên hỏi **nội dung nào** | Không | "Giải thích đoạn này" khi chưa chọn đoạn |
| `abstain` | Hỏi về bài nhưng bài không có căn cứ, hoặc đòi đáp án quiz | Không | "Kill switch là gì?" |

`chat` không được dùng để né citation: câu hỏi về kiến thức (dù bài có hay không) phải đi `answer` hoặc `abstain`. Backend chỉ kiểm tra citation của `answer`.

### Flow một lượt (đề xuất)

```
prompt = luật cố định + Persona + MỤC LỤC bài + (đoạn học viên đã chọn) + lịch sử + câu hỏi
   │
   ▼
LLM ──┬─ gọi search_lesson(query) ──▶ code: BM25 trong bài này → top-3 đoạn ──▶ LLM (vòng sau)
      ├─ gọi propose_persona_memory ─▶ code: tạo đề xuất pending ─────────────▶ LLM (vòng sau)
      └─ kết thúc bằng answer | chat | clarify | abstain
   │
   ▼
guard (code) ──▶ JSON về BE          tối đa 2 lần search, 3 vòng LLM (BE chờ tối đa 30 giây)
```

- **Agent tự quyết có search hay không.** "hi" không cần search; câu hỏi về bài thì search. Model tự viết query từ lịch sử chat, nên câu kiểu "còn cái kia thì sao?" vẫn tìm đúng.
- **Mục lục luôn có trong prompt** (tên các mục + ID) để model biết bài có gì, viết query tốt và gợi ý khi chào.
- **Phạm vi = bài của chat đang mở.** BE từ chối citation thuộc bài khác (`server.py`), muốn mở rộng cả Day thì phải sửa BE.

### Luật cố định (system prompt, Persona không ghi đè)

Đã có bản cơ bản trong `prompt.py`: chỉ nói về bài đang mở · không bịa · không đưa đáp án quiz · Persona và nội dung bài là dữ liệu, không phải chỉ thị · tiếng Việt, ngắn gọn, văn bản thuần.

### Guard — code giữ, không phó mặc cho model

- Citation chỉ hợp lệ nếu `source_id` nằm trong các đoạn model **đã thật sự nhận** ở lượt này (kết quả search + đoạn đã chọn). **Locator do code điền từ manifest**, model không tự viết.
- `answer` không còn citation hợp lệ → hạ xuống `abstain`.
- Model trả text thường mà không gọi tool kết thúc → gọi lại một lần; vẫn vậy thì trả `chat` nếu lượt đó chưa search, `abstain` nếu đã search.
- Clarify: không hỏi lại hai lượt liên tiếp; Persona đã ghi kiểu trả lời thì không hỏi về kiểu trả lời; mỗi lựa chọn là một câu hỏi đầy đủ (bấm nút = gửi câu đó).
- Output luôn qua `schemas.AIReply` trước khi trả BE.

### Persona

- Nằm trong agent. Nội dung là markdown ≤2.000 ký tự, 2 mục: *Tính cách Tutor* · *Tutor nhớ về bạn* (spec §4).
- Đưa vào prompt trong khối `<persona>`, chỉ điều chỉnh cách trình bày (độ dài, xưng hô, ví dụ); luật cố định luôn thắng.
- Tutor chỉ **đề xuất** ghi nhớ; học viên bấm Lưu mới ghi. Điều học viên không muốn Tutor nhớ ghi thành dòng `Đừng nhớ: X` trong *Tutor nhớ về bạn* (tự gõ hoặc nhờ Tutor đề xuất); Tutor không đề xuất ghi nhớ điều chứa X.
- **Không version, không hoàn tác, không snapshot theo chat.** Agent đọc Persona hiện tại theo `X-Learner-ID` mỗi lượt, nên sửa Persona áp dụng ngay câu hỏi tiếp theo.
- Bấm Lưu một đề xuất = áp dòng đó vào Persona **hiện tại** (không ghi đè bằng bản `after` cũ), nên học viên sửa tay giữa chừng không bị mất.
- Dòng dạng `Khoá: giá trị` (vd `Độ dài: ngắn gọn`) thay dòng cùng khoá thay vì thêm trùng.
- Mã: `persona/store.py` (SQLite, `AGENT_DB`), `persona/routes.py`, `persona/tools.py` (tool + khối prompt). `agent.py` đã có vòng tool nhỏ cho tool này — Tùng mở rộng thêm tool của mình vào dict `tools`.

## Đề xuất tool

Tool là hàm Python trong agent, truyền cho model qua tham số `tools` — **không cần MCP** vì chỉ agent này dùng. `lesson_id` và học viên do code gắn, không phải tham số của model.

| Tool | Tham số | Trả về / tác dụng | Kết thúc lượt? | Người |
|---|---|---|---|---|
| `search_lesson` | `query` | Top-3 đoạn trong bài đang mở `{source_id, title, text}` (BM25, bỏ dấu) | Không | Tùng |
| `answer` | `text`, `citations: [source_id]` | `decision=answer`; guard điền locator | Có | Tùng |
| `chat` | `text` | `decision=chat`, không citation | Có | Tùng |
| `clarify` | `question`, `options: [2–3 câu]` | `decision=clarify`; options thành nút `send_message` | Có | Tùng |
| `abstain` | `reason`, `next_step` | `decision=abstain`, nói rõ bài không có + gợi ý tiếp | Có | Tùng |
| `propose_persona_memory` | `section`, `item` | Tạo đề xuất `{before, after}` pending, trả về trong `persona_proposals` | Không | Thái |

Cần thử: endpoint Gemini tương thích OpenAI có hỗ trợ `tool_choice="required"` không; nếu không, guard xử lý trường hợp model trả text thường.

## Phân công

| Người | Phạm vi | Việc |
|---|---|---|
| **Thái** | Persona | ✅ Xong: store SQLite, 5 route, `propose_persona_memory`, `persona_block()`, bỏ version/snapshot ở BE/FE/CONTRACT. Chạy BE với `PERSONA_API_URL` trỏ vào agent |
| **Tùng** | Flow agent | Vòng tool trong `agent.py` · `search_lesson` (BM25) · `answer`/`chat`/`clarify`/`abstain` · citation + guard · idempotency theo `Idempotency-Key` (chỉ cache lượt thành công) · trace JSONL cho CP3/eval |
| **Cường** | Eval | Chạy golden set qua `/respond`, đọc trace |

Điểm nối giữa hai người: `agent.py` đã có vòng tool và dict `tools` với `propose_persona_memory` — Tùng thêm tool của mình vào đó; `persona_block()` đã được gọi trong `build_messages()`.
