# Contract nối AI và Persona

Đây là contract adapter của ứng dụng, cần đối chiếu với implementation phía nhóm AI/Persona trước khi nối live. `models.py` là schema chuẩn và `/openapi.json` mô tả API ứng dụng. FE gọi cùng origin `/api/*`; các route Persona là proxy, không chứa nghiệp vụ nhớ/quên.

## Danh tính và lỗi

BE gửi `X-Learner-ID` lấy từ session phía server, không lấy learner ID từ browser. Nếu cấu hình key, gửi `Authorization: Bearer ...`. Upstream chỉ được tin header danh tính từ BE đã xác thực, không mở công khai cho client tự khai owner.

Timeout 30 giây; không follow redirect; lỗi kỹ thuật là 502/503/504, khác quyết định `abstain`. Persona service phải kiểm tra owner và trạng thái proposal nguyên tử. Accept/reject phải idempotent để chịu lỗi mạng hoặc crash giữa upstream và database ứng dụng.

## AI: POST /respond

Request gồm `request_id` (khóa yêu cầu AI do BE quản lý), `chat_id`, `lesson_id`, `text`, `history` (role/text lấy từ DB), `selected_source_ids`. Không gửi Persona: agent tự đọc Persona hiện tại theo `X-Learner-ID` mỗi lượt. Header `Idempotency-Key` bằng `request_id`. BE lưu khóa trong SQLite: giữ nguyên khi timeout/5xx hoặc lỗi lưu DB; đổi khóa sau phản hồi vi phạm contract (JSON/schema/citation/proposal). Upstream phải tái sử dụng kết quả cùng key. ID lượt trong ứng dụng và `client_request_id` của FE vẫn giữ nguyên, không nhân đôi tin nhắn. Chỉ retry lượt cuối để không đưa lịch sử tương lai vào lượt cũ; lỗi 409 hướng người dùng gửi thành câu hỏi mới.

Response:

```json
{
  "decision": "answer",
  "text": "Nội dung phản hồi",
  "citations": [{"source_id": "demo-grounding--kiem-chung", "locator": "mock-lessons/demo-grounding.md#kiem-chung"}],
  "actions": [{"label": "Giải thích thêm", "type": "send_message", "value": "Giải thích thêm"}],
  "persona_proposals": []
}
```

`decision`: answer/chat/clarify/abstain. Answer phải có citation. `chat` là trả lời thường không cần citation (chào hỏi, cảm ơn, câu không liên quan bài); FE không gắn badge. `locator` là chuỗi đường dẫn Markdown + `#anchor` đúng nguồn do loader tạo, không phải URL do model dựng. Actions chỉ gồm send_message hoặc open_source (value là source ID).

Proposal: `{id,before,after}`. ID gồm chữ/số/gạch ngang, tối đa 80 ký tự. AI/Persona service phải đăng ký proposal theo owner trước khi trả ID. Text Persona tối đa 2.000 ký tự. Không tự lưu proposal; giữ luật system/citation/quiz ở phía AI. Không để Persona ghi đè luật cố định.

## Persona service

| Route | Request | Response |
|---|---|---|
| GET /persona | owner header | `{text,updated_at}` |
| PUT /persona | `{text}` | Persona mới |
| DELETE /persona/memory | không body | Persona mới, chỉ xoá mục ghi nhớ |
| POST /persona/proposals/{id}/accept | `{edited_text}`; null thì áp dòng đề xuất vào Persona **hiện tại** | Persona mới |
| POST /persona/proposals/{id}/reject | `{}` | JSON xác nhận; không đổi Persona |

Không có version hay hoàn tác: lần ghi sau thắng. `updated_at` là chuỗi thời gian hiển thị. Không snapshot theo chat: sửa Persona áp dụng từ câu hỏi tiếp theo. Persona service hiện nằm trong agent (`codebase/agent/persona/`).

Các mục Persona và chính sách dữ liệu nhạy cảm do Persona owner xử lý. Xoá memory chỉ xoá mục ghi nhớ trong Persona, không xoá lịch sử chat. Cần quyết định chính sách retention trước khi cung cấp thao tác “quên toàn bộ” theo nghĩa xoá dữ liệu.

## Nguồn bài

Manifest là JSON array bài `{id,day,title,subtitle,sample,markdown}`. `markdown` là đường dẫn `.md` tương đối bên trong thư mục manifest, không cho thoát thư mục. File demo nằm trong `mock-lessons/`, là nội dung tự viết; không dùng học liệu VLearn thật và không commit `data/`.

Mỗi H2 có cú pháp `## Tên mục {#anchor-on-dinh}`. Loader sinh source `{id,kind,locator,anchor,label,title,text}`: `id = lesson_id + "--" + anchor`, `kind = markdown`, `locator = markdown + "#" + anchor`. Nội dung source kéo dài đến H2 tiếp theo. Các ID bài/source phải duy nhất. Giữ anchor ổn định khi sửa tiêu đề; thay anchor sẽ thay định danh citation.

Demo render H1, H2, đoạn văn và danh sách gạch đầu dòng bằng DOM/textContent; không thực thi HTML. FE mở dialog đúng đoạn và scroll/highlight heading tương ứng. Nhóm retrieval cần dùng cùng IDs/locator từ `GET /api/lessons/{id}`; chưa có PDF/video viewer hoặc đồng bộ portal thật.

## Lịch sử hội thoại ứng dụng

`GET /api/chats` cần session, trả `{id,lesson_id,title,created_at}` theo thời gian tạo mới nhất trước, chỉ trong owner hiện tại. Mở một item bằng `GET /api/chats/{id}` để khôi phục bài và tin nhắn. Tin nhắn user có `retryable` để FE chỉ hiện retry trực tiếp cho lượt lỗi cuối.

Exception bất ngờ được chuyển thành lỗi kỹ thuật, đưa lượt hỏi về `failed`. Nếu SQLite đang khóa khi dọn trạng thái, single-worker giữ thao tác dọn trong bộ nhớ và áp dụng trước lần truy cập DB kế tiếp; nếu process dừng, startup chuyển pending sang failed. Database còn bị khóa sẽ báo lỗi, không trả trạng thái pending giả là đang gọi AI.
