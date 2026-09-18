# Kiểm soát độ tin cậy và Xử lý ranh giới tri thức trong hệ thống RAG

## Kiến trúc RAG và Dẫn nguồn kiểm chứng {#kiem-chung}

Kiến trúc RAG (Retrieval-Augmented Generation) kết hợp giữa bộ truy xuất dữ liệu (Retrieval) và mô hình ngôn ngữ lớn (LLM). Khi người dùng đặt câu hỏi, hệ thống sẽ tìm kiếm các đoạn thông tin liên quan nhất từ kho tri thức để đưa vào ngữ cảnh (context) cho mô hình sinh câu trả lời.

Một citation (dẫn nguồn) chuẩn là bằng chứng giúp người học đối chiếu câu trả lời của AI với nội dung bài học gốc. Việc trích dẫn minh bạch giải quyết vấn đề lớn nhất của LLM là người dùng không biết thông tin bắt nguồn từ đâu.

- Đọc phát biểu được tổng hợp bởi trợ giảng AI.
- Mở đoạn trích dẫn (citation) được đính kèm câu trả lời.
- Đối chiếu xem đoạn văn bản gốc có thực sự chứng minh phát biểu hay không.

## Xử lý ngoài phạm vi (Out-of-Domain) và Từ chối an toàn {#thieu-can-cu}

Trong các hệ thống RAG thực tế, việc xử lý các câu hỏi nằm ngoài phạm vi tri thức (Out-of-Domain) là tối quan trọng. Nếu bài học không chứa câu trả lời, mô hình bắt buộc phải chọn phương án từ chối (abstain) thay vì cố gắng suy đoán hoặc bịa đặt thông tin.

Nếu câu hỏi quá ngắn hoặc không rõ nghĩa (ví dụ "giải thích đoạn này"), trợ giảng cần chủ động hỏi lại (clarify) để xác định mục tiêu học tập của người dùng.

- Không tự ý phỏng đoán khi tài liệu hiện tại không đề cập.
- Từ chối lịch sự và gợi ý các chủ đề có sẵn trong bài.
- Yêu cầu học viên cung cấp thêm ngữ cảnh khi câu hỏi mơ hồ.

## Ảo giác của mô hình và cách hạn chế {#ao-giac}

Ảo giác (Hallucination) là hiện tượng mô hình ngôn ngữ lớn tự tin đưa ra các thông tin hoàn toàn sai lệch hoặc không có căn cứ thực tế. Nguyên nhân là do LLM hoạt động theo cơ chế dự đoán từ tiếp theo dựa trên xác suất thống kê chứ không thực sự suy luận như con người.

Kỹ thuật Grounding giúp neo chặt nội dung câu trả lời vào bằng chứng tài liệu được cung cấp. Bằng cách kết hợp RAG với lớp kiểm duyệt code guardrails, hệ thống có thể phát hiện và loại bỏ các phát biểu thiếu trích dẫn trước khi trả về cho người dùng.
