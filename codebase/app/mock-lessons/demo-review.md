# Ôn tập chủ động

## Tự nhớ trước khi mở bài {#tu-nho}

Golden Set (tập dữ liệu kiểm thử vàng) là tập hợp các câu hỏi điển hình kèm theo đáp án chuẩn đã được con người thẩm định kỹ lưỡng. Trong quy trình phát triển sản phẩm AI, việc xây dựng Golden Set tối thiểu 20 câu hỏi là bước bắt buộc để đo lường độ chính xác thực tế thay vì đánh giá bằng cảm tính.

Một bộ Golden Set tiêu chuẩn cần bao phủ đa dạng các kịch bản: câu hỏi trả lời được, câu hỏi ngoài phạm vi, câu hỏi mơ hồ và các trường hợp cố tình phá vỡ quy tắc (jailbreak).

- Tuyển chọn các câu hỏi thực tế từ người dùng thật.
- Gắn nhãn kết quả mong đợi (Ground Truth) cho từng trường hợp.
- Chạy kiểm thử tự động toàn bộ tập dữ liệu sau mỗi lần sửa đổi prompt hoặc code.

## Chọn bước tiếp theo {#ke-hoach}

Để đánh giá một hệ thống RAG và trợ giảng AI toàn diện, các kỹ sư cần theo dõi 4 chỉ số cốt lõi:

- Độ trung thực (Faithfulness): Câu trả lời có bám sát và có bằng chứng trong tài liệu nguồn hay không.
- Độ phù hợp (Answer Relevance): Nội dung trả lời có giải quyết đúng trọng tâm câu hỏi của người dùng hay không.
- Độ chính xác trích dẫn (Citation Precision): Trích dẫn có mở đúng đoạn văn bản chứa dữ kiện hay không.
- Độ trễ (Latency) và Chi phí token: Thời gian phản hồi có đảm bảo trải nghiệm người dùng mượt mà hay không.

## Đánh giá bằng LLM-as-a-Judge {#llm-as-judge}

Phương pháp LLM-as-a-Judge sử dụng một mô hình ngôn ngữ lớn mạnh mẽ (như GPT-4o hoặc Gemini 1.5 Pro) đóng vai trò làm giám khảo chấm điểm tự động các câu trả lời dựa trên bộ tiêu chí (rubric) định sẵn.

Giải pháp này giúp tự động hóa quy trình đánh giá hàng nghìn lượt hội thoại một cách nhanh chóng, tiết kiệm thời gian và chi phí so với việc kiểm tra thủ công bằng con người.
