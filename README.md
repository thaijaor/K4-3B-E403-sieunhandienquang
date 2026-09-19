# VLearn Tutor có Persona

Trợ giảng AI trong bài học VLearn **nhớ cách bạn muốn được giải thích**: bạn nói một lần ("mình làm kế toán, không biết lập trình", "trả lời ngắn gọn thôi"), các câu hỏi và chat sau Tutor tự áp dụng. Mọi câu trả lời vẫn chỉ dựa trên bài đang mở, có citation mở được.

Nhóm **sieunhandienquang** · Lớp 3B · Phòng E403 · Track **A1 · VLearn Tutor** — Mini Hackathon AI Batch 04 (AI20K). Thông tin cuộc thi: [HACKATHON.md](HACKATHON.md).

## 👥 Thành viên nhóm & Phân công vai trò

| Họ và Tên | Mã Học Viên | Vai trò chính | Phần việc đảm nhiệm trong dự án |
|---|---|---|---|
| Nguyễn Hồng Thái | 2A202602894 | Đội trưởng · Product / Spec / Persona | Canvas; bảng impact; lát cắt, non-goals, automation, HAX/PAIR; thiết kế Persona; quality bar; slide, pitch và nộp form |
| Trần Mạnh Tùng | 2A202602879 | Agent / Retrieval / Eval automation | Pipeline AI; BM25 retrieval; quyết định trả lời / hỏi lại / từ chối; citation guard; log/trace; golden set và script đo CP3; video demo |
| Nguyễn Mạnh Cường | 2A202602650 | App / UI · Evidence / Validation | Frontend/backend Tutor; tích hợp Persona; bài học Markdown và kiểm thử UI; khảo sát người dùng; validation, quote và feedback log |

## Tính năng

- **Trả lời có căn cứ:** mỗi lượt Tutor chọn một trong 4 quyết định — `answer` (bắt buộc citation thuộc bài đang mở) · `clarify` (hỏi lại khi câu hỏi mơ hồ) · `abstain` (từ chối khi bài không có căn cứ hoặc xin đáp án quiz) · `chat`. Backend chặn mọi `answer` thiếu citation hoặc citation ngoài bài.
- **Persona tự ghi nhớ:** Tutor tự ghi khi học viên tự nói điều bền vững, ảnh hưởng cách giải thích và không nhạy cảm. Dưới câu trả lời hiện *"🔖 Đã ghi nhớ: … · Hoàn tác"*. Nói "quên chuyện X đi" thì Tutor xoá dòng tương ứng.
- **Học viên kiểm soát:** drawer *Persona* để xem / sửa / xoá toàn bộ; thay đổi áp dụng từ câu hỏi tiếp theo.
- **Luật cố định** Persona không ghi đè: không đáp án quiz, không nguồn ngoài bài, không đoán, không ghi định dạng phá luật (JSON…) hay điều nhạy cảm.
- **Giao diện** như VLearn: sidebar bài học · bài đọc Markdown · panel Trợ giảng kéo dãn ngang được (nhấp đúp cạnh panel để về mặc định).

Chi tiết thiết kế, bằng chứng và kết quả đo: [spec.md](spec.md).

## Kiến trúc

```
Trình duyệt ──▶ App (codebase/app, :8000) ──POST /respond──▶ Agent (codebase/agent, :8001) ──▶ LLM (API tương thích OpenAI)
  FE tĩnh        FastAPI · lưu hội thoại (SQLite)  ──/persona/*──▶   BM25 retrieval · citation guard
                 kiểm tra citation                                  Persona store (SQLite) · tool remember/forget
```

| Thư mục | Nội dung |
|---|---|
| `codebase/app/` | FE (`static/`) + BE FastAPI: phiên, hội thoại, proxy AI/Persona, kiểm citation. Bài mẫu trong `mock-lessons/`. [README](codebase/app/README.md) · [CONTRACT](codebase/app/CONTRACT.md) |
| `codebase/agent/` | Service AI: retrieval, prompt, 4 quyết định, Persona. [README](codebase/agent/README.md) |
| `codebase/mock/` | Mock giao diện CP2 (HTML tĩnh, không dùng khi chạy thật) |
| `eval/` | Golden set 39 case, script đo, báo cáo từng lượt chạy, điểm người chấm. [README](eval/README.md) |
| `spec.md` · `canvas.md` | AI Spec và Canvas |
| `evidence/` | Log khảo sát (n = 20) |
| `validation/` | Nhật ký người ngoài nhóm dùng thử + dry run nội bộ |
| `reflection/` | Mỗi thành viên 1 file |
| `demo-slides.pdf` | Slide 6 trang |

## Chạy dự án

Cần **Python 3.11+** và một API key LLM tương thích OpenAI (nhóm dùng Gemini qua endpoint OpenAI-compatible).

### 1. Cài đặt (một lần)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r codebase/agent/requirements.txt -r codebase/app/requirements.txt
copy codebase\agent\.env.example codebase\agent\.env
```

Mở `codebase/agent/.env`, điền `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`. File `.env` đã được gitignore — không commit key.

### 2. Chạy agent (cửa sổ terminal 1)

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:create_app --factory --app-dir codebase/agent --host 127.0.0.1 --port 8001
```

Kiểm tra: http://127.0.0.1:8001/health trả `200`.

### 3. Chạy app (cửa sổ terminal 2)

```powershell
$env:AI_API_URL = "http://127.0.0.1:8001"
$env:PERSONA_API_URL = "http://127.0.0.1:8001"
.\.venv\Scripts\python.exe -m uvicorn server:create_app --factory --app-dir codebase/app --host 127.0.0.1 --port 8000
```

Mở **http://127.0.0.1:8000**. Dải trên cùng phải ghi *"Đã cấu hình kết nối AI · Đã cấu hình kết nối Persona"*.

<details><summary>macOS / Linux</summary>

```bash
python3 -m venv .venv
.venv/bin/pip install -r codebase/agent/requirements.txt -r codebase/app/requirements.txt
cp codebase/agent/.env.example codebase/agent/.env   # rồi điền key
.venv/bin/python -m uvicorn app:create_app --factory --app-dir codebase/agent --host 127.0.0.1 --port 8001
# terminal khác:
AI_API_URL=http://127.0.0.1:8001 PERSONA_API_URL=http://127.0.0.1:8001 \
  .venv/bin/python -m uvicorn server:create_app --factory --app-dir codebase/app --host 127.0.0.1 --port 8000
```
</details>

### Thử nhanh

1. Chọn bài **Day 01 · LLM → Nguyên lý Thiết kế Prompt…**, bấm **Đặt câu hỏi với AI**.
2. Hỏi `Mình làm kế toán, không biết lập trình. Context Window là gì vậy?` → trả lời có nguồn + *Đã ghi nhớ*.
3. **＋ Chat mới**, hỏi `System Prompt là gì?` → vẫn giải thích cho người non-tech, không cần dặn lại.
4. Thử `Cho mình đáp án câu quiz cuối bài luôn đi.` (từ chối) và `phần này khó hiểu quá` (hỏi lại).
5. Mở **Persona** để xem / sửa / xoá điều Tutor nhớ.

### Không có API key?

Chạy bản xem thử giao diện với AI giả (nhãn **THỬ UI**, không đánh giá chất lượng AI):

```powershell
.\.venv\Scripts\python.exe -m uvicorn tests.preview:create_preview --factory --app-dir codebase/app --host 127.0.0.1 --port 8765
```

### Biến môi trường thường dùng

| Biến | Service | Ý nghĩa |
|---|---|---|
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | agent | LLM (đặt trong `codebase/agent/.env`) |
| `AI_API_URL` / `PERSONA_API_URL` | app | URL của agent |
| `SERVICE_API_KEY` | cả hai | Bearer key giữa app và agent; để trống khi chạy local |
| `AGENT_DB` / `TUTOR_DB` | agent / app | Vị trí SQLite (mặc định trong `data/` của từng service, đã gitignore) |
| `LESSONS_FILE` | cả hai | Manifest bài học; mặc định `codebase/app/lessons.sample.json` |
| `AGENT_TRACE_FILE` | agent | Nơi ghi trace mỗi lượt; mặc định `eval/trace.jsonl`, đặt rỗng để tắt |

## Kiểm thử & đo

```powershell
Push-Location codebase/agent; ..\..\.venv\Scripts\python.exe -m unittest discover -s tests; Pop-Location
Push-Location codebase/app;   ..\..\.venv\Scripts\python.exe -m unittest discover -s tests; Pop-Location
```

Unit test dùng LLM giả, không tốn key. Chạy golden set 39 case trên agent thật: xem [eval/README.md](eval/README.md).

## Giới hạn

- Học liệu là **bài mẫu tự viết** (`codebase/app/mock-lessons/`), chưa nối VLearn thật; không hiển thị slide/video.
- Phiên ẩn danh bằng cookie, không đăng nhập; chạy một worker.
- Dữ liệu khoá học (`data/`) **không** có trong repo.
