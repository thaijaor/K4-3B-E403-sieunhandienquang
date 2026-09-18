# Nguyên lý Thiết kế Prompt và Tối ưu Ngữ cảnh cho LLM

## System Prompt {#system-prompt}

System Prompt (lời nhắc hệ thống) là chỉ dẫn nền tảng được gửi kèm trong mỗi yêu cầu gửi tới LLM. System Prompt đóng vai trò là "hiến pháp" của AI: xác định vai trò, giọng điệu, phong cách giao tiếp và thiết lập các nguyên tắc cố định không thể bị người dùng ghi đè.

Trong ứng dụng trợ giảng, System Prompt giúp mô hình hiểu rằng nó phải đóng vai một người hướng dẫn sư phạm, chỉ trả lời dựa trên bài học đang mở và tuyệt đối không làm bài hộ học viên.

- Thiết lập vai trò rõ ràng (Persona) cho trợ giảng.
- Đặt ra các nguyên tắc bắt buộc: không giải quiz, không bịa nguồn.
- Định hướng phong cách trả lời ngắn gọn, trực diện, không dài dòng.

## Context Window {#context-window}

Context Window (cửa sổ ngữ cảnh) là giới hạn số lượng token mà LLM có thể tiếp nhận và xử lý trong một lượt tương tác. Kỹ thuật Context Injection đưa các đoạn trích từ bài học vào cửa sổ ngữ cảnh để mô hình có cơ sở dữ liệu làm việc.

Khi đặt câu hỏi, nếu bạn biết cách cô đọng ngữ cảnh và diễn đạt lại vấn đề bằng từ khóa chuyên môn, mô hình sẽ hiểu chính xác điểm nghẽn và đưa ra giải pháp trọng tâm hơn.

- Nhận diện giới hạn token để tránh đưa ngữ cảnh thừa thãi.
- Lọc bỏ các thông tin rác trước khi đưa vào context.
- Diễn đạt lại yêu cầu rõ ràng để kích hoạt tri thức liên quan của mô hình.

## Prompt Engineering {#prompt-engineering}

Kỹ thuật Prompt Engineering chuyên nghiệp thường áp dụng cấu trúc 3 phần để đảm bảo tính nhất quán của câu trả lời:

- Vai trò (Role): Xác định rõ danh tính (ví dụ: Chuyên gia Trí tuệ Nhân tạo).
- Ngữ cảnh (Context): Cung cấp tài liệu tham khảo và lịch sử trò chuyện.
- Ràng buộc và Định dạng (Constraints & Format): Yêu cầu định dạng cụ thể (văn bản thuần, JSON, danh sách gạch đầu dòng) và giới hạn số từ tối đa.
