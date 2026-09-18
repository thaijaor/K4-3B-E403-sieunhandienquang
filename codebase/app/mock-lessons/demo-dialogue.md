# Trao đổi với trợ giảng

## Hỏi tiếp có mục đích {#hoi-tiep}

Khác với các chatbot LLM đơn thuần chỉ sinh văn bản tĩnh, AI Agent là hệ thống thông minh sở hữu khả năng tự lập kế hoạch (Planning), ghi nhớ ngữ cảnh dài hạn (Memory) và chủ động sử dụng công cụ (Tool Use) để giải quyết các mục tiêu phức tạp trong môi trường thực tế.

Trong bài toán trợ giảng, Agent tự quyết định khi nào cần tra cứu nội dung bài học, khi nào cần hỏi lại người dùng và khi nào phải từ chối các yêu cầu vi phạm quy tắc đạo đức học thuật.

- Tự chủ lựa chọn công cụ phù hợp với câu hỏi của người dùng.
- Duy trì trạng thái hội thoại và mục tiêu sư phạm xuyên suốt các lượt chat.
- Thích ứng linh hoạt với trình độ và phong cách của từng học viên.

## Kiểm tra câu trả lời {#kiem-tra}

Mô hình ReAct (Reasoning + Acting) là kiến trúc cốt lõi của các hệ thống AI Agent hiện đại. Quy trình hoạt động tuần tự gồm ba pha liên hoàn:

- Suy nghĩ (Thought): Mô hình tự phân tích câu hỏi và lập kế hoạch bước đi tiếp theo.
- Hành động (Action): Mô hình gọi công cụ (Tool Calling/Function Calling), ví dụ gọi hàm tìm kiếm bài học `search_lesson`.
- Quan sát (Observation): Mô hình nhận kết quả trả về từ công cụ và tiếp tục chu trình cho đến khi đạt được kết quả cuối cùng.

## Guardrails và An toàn AI {#guardrails-an-toan}

Guardrails (hàng rào bảo vệ) là lớp mã nguồn độc lập bao bọc xung quanh mô hình AI nhằm đảm bảo hệ thống vận hành an toàn và tin cậy:

- Kiểm soát đầu vào (Input Guard): Phát hiện và vô hiệu hóa các nỗ lực tấn công bẻ khóa (Jailbreak) hoặc tiêm lệnh (Prompt Injection).
- Kiểm soát đầu ra (Output Guard): Kiểm tra tính hợp lệ của trích dẫn citation, ngăn chặn câu trả lời lộ đáp án bài kiểm tra và lọc bỏ nội dung phản cảm.
- Bảo vệ dữ liệu nhạy cảm: Ẩn danh hóa thông tin cá nhân của học viên trước khi chuyển tiếp cho mô hình xử lý.
