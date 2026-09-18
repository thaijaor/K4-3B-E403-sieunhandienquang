# Học liệu AI/LLM cơ bản và kịch bản thử Persona

## Phạm vi và nguồn biên soạn

Sáu bài tiếng Việt tự viết, ba ngày × hai bài; mỗi bài 600–900 đơn vị tách bằng khoảng trắng (cách đếm kỹ thuật, không phải phân đoạn từ tiếng Việt). Có mục tiêu, ví dụ đời thường/kỹ thuật, giới hạn, thực hành mở, tóm tắt và ba câu hỏi. Không phải học liệu chính thức VLearn; không sao chép data pack. Ví dụ câu lạc bộ, biểu mẫu và cửa hàng là giả định do nhóm biên soạn, không phải dữ liệu khảo sát.

Nguồn đối chiếu khái niệm khi biên soạn ngày 18/09/2026:

- Token, mô hình ngôn ngữ: [Google ML Crash Course](https://developers.google.com/machine-learning/crash-course/llm).
- Giới hạn mô hình sinh: [Google — What's a large language model?](https://developers.google.com/machine-learning/crash-course/llm/transformers).
- Yêu cầu rõ và ví dụ: [Anthropic — Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents). Không sao chép ví dụ của hãng.
- Temperature/lấy mẫu: [Google Cloud — GenerationConfig](https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1beta1/GenerationConfig).
- Grounding: [Google Cloud — Generative AI glossary](https://docs.cloud.google.com/docs/generative-ai/glossary). Phạm vi chỉ bài đang mở là quy tắc riêng của prototype, không phải định nghĩa chung của grounding.
- Persona/snapshot/quyền xác nhận: thiết kế dự án tại [PR #5](https://github.com/thaijaor/K4-3B-E403-sieunhandienquang/pull/5), đối chiếu commit `f40e3ab2a521ef95cbad421882a3c5cc668d2460`. Không tuyên bố đây là chức năng đã tích hợp service thật.

Các nguồn trên dùng để biên soạn và kiểm tra, không tự động thêm vào nguồn retrieval của Tutor. Citation trong app vẫn chỉ trỏ đến đoạn của bài đang mở. Markdown chỉ dùng H1, H2 có anchor, đoạn văn và danh sách; không cần thư viện mới.

## Chạy 12 kịch bản

`lesson-scenarios.json` là bộ bổ sung, không thay golden set, chất lượng chuẩn hay kết quả khảo sát của nhóm. Mỗi case có ID, lesson_id, Persona, câu hỏi, quyết định mong đợi, anchor và tiêu chí đọc duyệt. `anchors` của case từ chối là nguồn để người chấm đối chiếu quy tắc, không bắt buộc câu từ chối phải có citation. Case trả lời phải có citation hỗ trợ từng khẳng định; trả lời với anchor có thật nhưng sai ý vẫn không đạt.

1. Dùng session thử riêng; mở bài theo lesson_id. Lưu Persona của case bằng giao diện rồi tạo chat mới, ghi phiên bản snapshot.
2. Không chọn đoạn ở L09. Các case khác có thể chọn đoạn được chỉ định; ghi lại nếu chọn để tái lập được lần thử.
3. Gửi nguyên văn câu hỏi, ghi quyết định, câu trả lời và citation thực tế. Đối chiếu nội dung từng nguồn, không chỉ kiểm tra URL tồn tại.
4. So sánh L07 và L08: cùng bài/câu hỏi, chat riêng, Persona khác. Cốt lõi kiến thức không thay đổi; cách giải thích phải khác phù hợp nhu cầu.
5. Trong L07, sửa Persona sang L08 khi chat cũ còn mở: phiên bản chat cũ không đổi. Tạo chat mới và gửi cùng câu hỏi, không nhắc lại phong cách trong câu hỏi; kiểm tra snapshot mới và cách trình bày. Việc service có đáp ứng phong cách cần AI thật để đánh giá.
6. Với L05, yêu cầu đề xuất nhớ một sở thích không nhạy cảm; chọn Không và kiểm tra Persona không đổi. Thử lại, đọc diff rồi Lưu; kiểm tra Hoàn tác và chat mới. Không ép service phải đề xuất cho mọi câu hỏi nếu điều kiện đề xuất chưa được teammate thống nhất.

Kết quả mỗi case ghi `CHƯA CHẠY`, `PASS`, `FAIL` hoặc `BLOCKED`, kèm loại service `double/live`, thời điểm, snapshot version và lý do. Mặc định toàn bộ đánh giá AI thật là **CHƯA CHẠY — chờ service AI/Persona**, không gán PASS từ preview. Mock chỉ xác minh luồng UI, trạng thái, nguồn và snapshot; không xác minh chất lượng câu trả lời.

## Tương thích và ranh giới

Giữ ID `demo-grounding`, `demo-question`, `demo-dialogue` cho các chủ đề tiếp nối; giữ các anchor `kiem-chung`, `thieu-can-cu`, `hoi-tiep`, `kiem-tra` cùng ý nghĩa. Chủ đề mới dùng `llm-basics`, `temperature`, `persona-basics`, không dùng lại ID cũ để giả một bài khác. Các file mẫu cũ không còn trong manifest vẫn được giữ; không xóa database/history. Chat gắn bài đã rút khỏi manifest có thể không mở lại được với manifest mới: dùng session mới cho đợt thử nội dung, không reset profile cũ; nếu cần xem lịch sử cũ, chạy manifest cũ trong bản checkout cũ. Không có migration dữ liệu trong phạm vi này.

Không sửa API/service AI hoặc Persona, không tự thêm mock vào server thật, không thêm quiz chấm điểm. Canvas CP1 và quality bar của nhóm giữ nguyên. Khi hợp nhất PR #5, chỉ chuyển phần bổ sung học liệu của `spec.md` vào §4 và dòng changelog vào §9; không chép đè evidence/phân công của teammate.
