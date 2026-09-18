# Thu Hoạch Cá Nhân — Trần Mạnh Tùng

- **Họ và tên:** Trần Mạnh Tùng
- **Mã học viên (MSSV):** `2A202602879`
- **Lớp:** 3B · **Phòng:** E403
- **Nhóm:** sieunhandienquang · **Track:** A1 — Tối ưu AI Tutor VLearn hiện có

---

## 1. Vai trò cá nhân trong nhóm

Trong dự án **Tutor nhớ cách trả lời học viên muốn (Persona)**, tôi đảm nhiệm vai trò **Agent/AI Pipeline**, phụ trách retrieval, quyết định trả lời–hỏi lại–từ chối, citation guard và bộ đo tự động ban đầu.

- **Agent:** hoàn thiện pipeline gọi AI và phân loại quyết định trung tâm theo nội dung bài đang mở.
- **Retrieval + Safety:** xây BM25 retrieval, kiểm tra citation và lưu trace để có thể kiểm chứng đường đi của từng câu hỏi.
- **Eval:** tạo golden set 20 case CP3, script chạy tự động và báo cáo kết quả lượt đầu trong [eval/](../eval/).

---

## 2. Phần việc trực tiếp phụ trách

1. **Hoàn thiện agent pipeline**

   - Xử lý bốn đường đi `answer`, `clarify`, `abstain`, `chat` thay vì luôn buộc model trả lời.
   - Kết nối bài học, prompt và model; lưu trace để biết retrieval trả đoạn nào, quyết định gì và citation nào được xuất ra.
   - Phần việc chính nằm ở commit `995ed33` và thư mục [codebase/agent/](../codebase/agent/).

2. **Xây retrieval và citation guard**

   - Dùng BM25 để truy xuất các đoạn liên quan trong bài đang mở.
   - Chỉ cho phép citation tồn tại trong nguồn đã retrieval; khi không đủ căn cứ, agent phải hỏi lại hoặc từ chối thay vì bịa nguồn.
   - Viết test cho quyết định, retrieval và guardrail để phát hiện lỗi sau mỗi lần đổi prompt hoặc dữ liệu bài học.

3. **Tạo lượt đo CP3**

   - Xây golden set 20 case, script chạy toàn bộ và báo cáo phần trăm thay vì mô tả “sản phẩm chạy tốt”.
   - Lưu cả case đạt và chưa đạt trong [eval/eval_report_cp3.md](../eval/eval_report_cp3.md), cùng trace phục vụ điều tra lỗi.
   - Phần eval CP3 được bổ sung trong commit `aee2279`.

---

## 3. Cách thức ứng dụng AI trong quá trình xây dựng

Tôi dùng AI để hỗ trợ nháp prompt, sinh khung test và rà soát các nhánh xử lý của agent. Mỗi đề xuất của AI đều phải qua test và trace vì chính model cũng có thể trả JSON sai, quyết định sai hoặc đưa citation không tồn tại.

1. AI hỗ trợ gợi ý các case thường, case mơ hồ và case guardrail; nhãn kỳ vọng được đối chiếu lại với spec và nội dung bài mẫu.
2. Khi chạy model thật, tôi lưu đầu vào, retrieval và đầu ra cần thiết để truy nguyên thay vì chỉ nhìn câu trả lời cuối.
3. Mock chỉ dùng cho test có kiểm soát; báo cáo phải phân biệt rõ mock với lần gọi model thật.

---

## 4. Một bài học thực tế rút ra từ chính các trường hợp thất bại của nhóm

### 🔴 Test có thể trượt vì nhãn và nội dung đã lệch nhau, không phải vì retrieval hỏng

- **Sự cố/giới hạn:** Ở lượt đo CP3, TC08 và TC09 bị kết luận sai vì agent trả `abstain`. Khi kiểm tra trace, retrieval vẫn trả đúng đoạn `demo-notes--ba-dong`; nguyên nhân là nội dung `demo-notes` đã đổi sang Chunking nhưng câu hỏi và nhãn cũ vẫn dựa trên nội dung trước đó.
- **Phân tích:** Nếu chỉ nhìn PASS/FAIL, nhóm dễ sửa nhầm thuật toán retrieval. Trace cho thấy lỗi thật nằm ở dữ liệu kiểm thử bị drift so với fixture bài học. Golden set, nguồn mẫu và nhãn kỳ vọng là một contract phải thay đổi cùng nhau.
- **Bài học rút ra:** Tôi học được rằng pipeline eval cần lưu đủ bằng chứng trung gian. Sau mỗi thay đổi nội dung hoặc prompt, phải chạy lại toàn bộ bộ đo và kiểm tra cả nhãn; không nên tối ưu code theo một con số fail khi chưa xác định đúng tầng gây lỗi.
