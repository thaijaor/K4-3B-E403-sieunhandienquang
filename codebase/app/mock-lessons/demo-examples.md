# Học qua ví dụ

## Bắt đầu bằng ví dụ nhỏ {#vi-du-nho}

Kỹ thuật Few-Shot Prompting (học qua ví dụ trong ngữ cảnh - In-Context Learning) là phương pháp cung cấp trực tiếp 2 đến 3 cặp mẫu (Đầu vào - Đầu ra mong muốn) ngay trong câu lệnh.

So với phương pháp Zero-Shot (không có ví dụ), Few-Shot giúp LLM nắm bắt ngay cấu trúc, phong cách hành văn và định dạng dữ liệu mong muốn mà không cần phải tinh chỉnh (fine-tune) trọng số mô hình.

- Cung cấp cặp ví dụ đầu vào và đầu ra mẫu trực quan.
- Chuẩn hóa định dạng câu trả lời theo khuôn mẫu cụ thể.
- Hướng dẫn mô hình cách tư duy trước khi đưa ra kết luận cuối cùng.

## Tìm một phản ví dụ {#phan-vi-du}

Phản ví dụ (Negative Examples) là kỹ thuật chỉ ra những câu trả lời sai hoặc không đạt yêu cầu để cảnh báo mô hình. Trong phát triển AI, việc huấn luyện mô hình bằng cả ví dụ đúng và phản ví dụ giúp hệ thống hiểu rõ biên giới logic và tránh các lỗi phổ biến.

- Đưa ra trường hợp vi phạm: Ví dụ trả lời không có dẫn nguồn.
- Chỉ ra nguyên nhân sai sót: Phát biểu thông tin không có trong tài liệu.
- Định hướng hành vi đúng: Bắt buộc hạ xuống từ chối (abstain) khi gặp trường hợp tương tự.

## Kỹ thuật Chain-of-Thought {#chain-of-thought}

Kỹ thuật Chuỗi suy luận (Chain-of-Thought - CoT) kích hoạt khả năng giải quyết vấn đề phức tạp bằng cách yêu cầu mô hình "hãy suy nghĩ từng bước" (Think step by step) trước khi chốt câu trả lời.

Phương pháp này phân rã câu hỏi lớn thành chuỗi các suy luận nhỏ có tính liên kết chặt chẽ, giảm đáng kể lỗi tính toán và logic suy diễn sai lệch trong các mô hình nền tảng.
