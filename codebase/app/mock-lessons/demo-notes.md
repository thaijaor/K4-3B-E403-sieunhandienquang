# Ghi chú sau khi đọc

## Ghi chú trong ba dòng {#ba-dong}

Kỹ thuật Chunking là quá trình chia nhỏ tài liệu dài thành các đoạn văn bản (chunk) có kích thước phù hợp trước khi lập chỉ mục vào cơ sở dữ liệu vector. Việc chọn kích thước chunk (chunk size) và độ trùng lặp (chunk overlap) ảnh hưởng trực tiếp đến chất lượng tìm kiếm thông tin.

Nếu chunk quá nhỏ, đoạn trích sẽ thiếu ngữ cảnh để LLM hiểu đúng. Nếu chunk quá lớn, kết quả tìm kiếm sẽ bị loãng và làm tăng chi phí token không cần thiết.

- Chunk size: Kích thước tối ưu thường dao động từ 200 đến 500 từ.
- Chunk overlap: Độ trùng lặp từ 10% đến 20% giúp bảo toàn ngữ cảnh ở ranh giới giữa các đoạn.
- Chunking theo cấu trúc: Ưu tiên tách đoạn theo tiêu đề H2, phân đoạn tự nhiên của bài học.

## Đối chiếu ghi chú {#doi-chieu}

Embeddings là biểu diễn toán học của văn bản dưới dạng các vector số thực nhiều chiều trong không gian ngữ nghĩa. Các đoạn văn bản có ý nghĩa tương đồng sẽ nằm gần nhau trong không gian vector.

Độ tương đồng Cosine (Cosine Similarity) là thuật toán đo góc giữa hai vector để xác định mức độ liên quan về mặt ngữ nghĩa giữa câu hỏi của học viên và các đoạn tài liệu trong cơ sở dữ liệu.

- Chuyển đổi văn bản thành vector bằng các mô hình Embedding chuyên dụng.
- Tính toán khoảng cách hoặc góc Cosine giữa vector câu hỏi và vector tài liệu.
- Xếp hạng và lấy ra các đoạn có điểm tương đồng cao nhất cho mô hình sinh lời đáp.

## Bộ nhớ ngắn hạn và dài hạn của AI {#bo-nho-ai}

Mô hình AI hiện đại được thiết kế với hai tầng lưu trữ thông tin:

- Bộ nhớ ngắn hạn (Short-term Memory): Nằm ngay trong Context Window của lượt chat hiện tại, lưu lại vài lượt hội thoại gần nhất.
- Bộ nhớ dài hạn (Long-term Memory): Được lưu trữ ngoài mô hình trong cơ sở dữ liệu (SQLite, Vector DB) dưới dạng Persona hoặc nhật ký học tập, giúp AI ghi nhớ phong cách học tập của học viên qua nhiều ngày.
