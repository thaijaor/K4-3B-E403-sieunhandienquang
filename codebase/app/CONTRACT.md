# Contract nối AI và Persona

Đây là contract adapter của ứng dụng, cần đối chiếu với implementation phía nhóm AI/Persona trước khi nối live. `models.py` là schema chuẩn và `/openapi.json` mô tả API ứng dụng. FE gọi cùng origin `/api/*`; các route Persona là proxy, không chứa nghiệp vụ nhớ/quên.

## Danh tính và lỗi

BE gửi `X-Learner-ID` lấy từ session phía server, không lấy learner ID từ browser. Nếu cấu hình key, gửi `Authorization: Bearer ...`. Upstream chỉ được tin header danh tính từ BE đã xác thực, không mở công khai cho client tự khai owner.

Timeout 30 giây; không follow redirect; lỗi kỹ thuật là 502/503/504, khác quyết định `abstain`. 409 nghĩa version conflict, FE giữ bản nháp. Persona service phải kiểm tra owner, version và trạng thái proposal nguyên tử. Accept/reject phải idempotent để chịu lỗi mạng hoặc crash giữa upstream và database ứng dụng.

## AI: POST /respond

Request gồm `request_id` (ID lượt phía BE), `chat_id`, `lesson_id`, `text`, `history` (role/text lấy từ DB), `selected_source_ids` và `persona` (null hoặc `{text,version,updated_at}`). Header `Idempotency-Key` là request_id, giữ nguyên khi retry. Upstream phải tái sử dụng kết quả cùng key.

Response:

```json
{
  "decision": "answer",
  "text": "Nội dung phản hồi",
  "citations": [{"source_id": "sample-01", "locator": "1"}],
  "actions": [{"label": "Giải thích thêm", "type": "send_message", "value": "Giải thích thêm"}],
  "persona_proposals": []
}
```

`decision`: answer/clarify/abstain. Answer phải có citation. `locator` là chuỗi page/segment_id đúng manifest, không phải URL do model dựng. Actions chỉ gồm send_message hoặc open_source (value là source ID).

Proposal: `{id,base_version,before,after}`. ID gồm chữ/số/gạch ngang, tối đa 80 ký tự. AI/Persona service phải đăng ký proposal theo owner trước khi trả ID. Text Persona tối đa 2.000 ký tự. Không tự lưu proposal; giữ luật system/citation/quiz ở phía AI. Không để Persona ghi đè luật cố định.

## Persona service

| Route | Request | Response |
|---|---|---|
| GET /persona | owner header | `{text,version,updated_at}` nhất quán tại cùng thời điểm |
| PUT /persona | `{text,expected_version}` | Persona mới |
| DELETE /persona/memory | `{expected_version}` | Persona mới, chỉ xoá mục ghi nhớ |
| POST /persona/proposals/{id}/accept | `{expected_version,edited_text}`; edited_text có thể null | Persona mới |
| POST /persona/proposals/{id}/reject | `{}` | JSON xác nhận; không đổi Persona |
| POST /persona/undo | `{target_version,expected_version}` | Khôi phục nội dung version đích bằng version mới |

Version là số nguyên tăng dần; updated_at là chuỗi thời gian hiển thị. Undo không được ghi đè thay đổi xảy ra sau version dự kiến. GET phải trả đồng bộ text/version; BE lưu trọn snapshot để các lượt sau không cần đọc Persona mới nhất.

Các mục Persona và chính sách dữ liệu nhạy cảm do Persona owner xử lý. Xoá memory hiện chỉ áp dụng Persona hiện tại, không xoá lịch sử chat/snapshot. Cần quyết định chính sách retention trước khi cung cấp thao tác “quên toàn bộ” theo nghĩa xoá dữ liệu.

## Nguồn bài

Manifest là JSON array bài `{id,title,subtitle,sample,sources}`. Mỗi source có `{id,kind,locator,label,title,text}`; IDs phải duy nhất toàn manifest. Cung cấp các đoạn đã được phép sử dụng, không đường dẫn file tuỳ ý. Nhóm retrieval cần dùng cùng source IDs/locator. Ứng dụng mở đoạn nguồn trong dialog; không có PDF viewer hoặc đồng bộ portal thật.
