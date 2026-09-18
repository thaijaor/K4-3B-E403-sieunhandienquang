# Thu Hoạch Cá Nhân — Nguyễn Mạnh Cường

- **Họ và tên:** Nguyễn Mạnh Cường
- **Mã học viên (MSSV):** `2A202602650`
- **Lớp:** 3B · **Phòng:** E403
- **Nhóm:** sieunhandienquang · **Track:** A1 — Tối ưu AI Tutor VLearn hiện có

---

## 1. Vai trò cá nhân trong nhóm

Trong dự án **Tutor nhớ cách trả lời học viên muốn (Persona)**, tôi đảm nhiệm phần **Ứng dụng Tutor + Evidence/Validation**, phụ trách frontend/backend, tích hợp Persona, khảo sát và lấy feedback từ người dùng ngoài nhóm.

- **Application:** xây giao diện đọc bài và panel AI Tutor, backend quản lý chat, Persona và contract tích hợp agent.
- **Reliability:** bổ sung lịch sử chat, retry an toàn, xử lý lỗi mạng/JSON/SQLite và kiểm thử nhiều viewport.
- **Evidence + Validation:** phụ trách khảo sát học viên, tổ chức hai phiên dùng thử ngoài nhóm, ghi quan sát, quote nguyên văn và quyết định sau feedback.

---

## 2. Phần việc trực tiếp phụ trách

1. **Khảo sát và chuẩn bị validation với người dùng**

   - Phụ trách thu khảo sát 20 học viên ngoài nhóm; 15/20 người xác nhận pain và 16/20 người đồng ý dùng thử prototype.
   - Chuẩn bị hai phiên validation với Lê Duy Quân và Võ Phú Hãn; task và nhật ký được tách riêng trong [validation/LeDuyQuan_2A202602731.md](../validation/LeDuyQuan_2A202602731.md) và [validation/VoPhuHan_2A202602628.md](../validation/VoPhuHan_2A202602628.md).
   - Chỉ ghi task, quan sát và quote sau phiên thử thực tế; không dùng AI hoặc suy đoán để lấp phần log còn trống.

2. **Xây ứng dụng Tutor end-to-end**

   - Tạo server, model dữ liệu, giao diện đọc bài, panel chat và Persona drawer.
   - Thiết kế contract để ứng dụng có thể nối với agent/Persona service nhưng vẫn dùng double có nhãn rõ khi kiểm thử UI.
   - Phần nền tảng ứng dụng được thực hiện trong commit `3f0b055` và thư mục [codebase/app/](../codebase/app/).

3. **Tăng độ tin cậy sau review**

   - Bổ sung bài học Markdown, danh sách lịch sử chat và cơ chế retry không làm mất hoặc nhân đôi lượt người dùng.
   - Kiểm tra owner isolation, lỗi timeout, JSON sai, SQLite bị khóa, phản hồi về muộn và trạng thái sau refresh.
   - Ghi ranh giới bằng chứng và kết quả test trong [codebase/app/VERIFICATION.md](../codebase/app/VERIFICATION.md); thay đổi chính nằm ở commit `b1319f3`.

4. **Chuẩn bị nội dung học và kiểm chứng chất lượng**

   - Tạo các bài học mẫu, source ID/locator và test để citation mở đúng đoạn, không đưa học liệu thật hoặc credential vào repo.
   - Kiểm tra bố cục desktop/mobile, thao tác mở–đóng–thu gọn chat, Persona và lịch sử.
   - Cùng Thái chấm 16 mục cần đánh giá bằng người ở lượt 2 và đối chiếu kết quả trước khi cập nhật báo cáo.

---

## 3. Cách thức ứng dụng AI trong quá trình xây dựng

Tôi dùng AI để hỗ trợ dựng khung frontend/backend, đề xuất tình huống lỗi và tạo test. Tuy nhiên, giao diện nhìn đúng hoặc test do AI viết chạy qua chưa đủ; tôi kiểm tra lại contract, trạng thái dữ liệu và hành vi trên nhiều kích thước màn hình.

1. Code AI đề xuất được giới hạn trong ranh giới ứng dụng và phải tuân theo contract chung với agent.
2. Các lỗi mạng, phản hồi muộn và SQLite khóa được chèn chủ động để kiểm tra recovery, không đợi lỗi xảy ra khi demo.
3. Nội dung bài học đều là dữ liệu giả tự viết; AI không được dùng để đưa dữ liệu thật, API key hoặc học liệu khóa học vào repo công khai.
4. Câu trả lời khảo sát, quan sát và quote validation phải đến từ người dùng thật; AI chỉ hỗ trợ soạn task và cấu trúc log.

---

## 4. Một bài học thực tế rút ra từ chính các trường hợp thất bại của nhóm

### 🔴 Một giao diện chạy được chưa đồng nghĩa luồng học tập đủ tin cậy

- **Sự cố/giới hạn:** Bản ứng dụng đầu tiên đã có frontend/backend và Persona integration, nhưng review cho thấy còn thiếu hỗ trợ bài Markdown đầy đủ, lịch sử chat và retry đáng tin cậy. Nếu request lỗi hoặc phản hồi cũ về muộn, người dùng có thể mất ngữ cảnh hoặc thấy trạng thái không khớp.
- **Phân tích:** Với Tutor, lỗi trải nghiệm không chỉ là bố cục xấu. Việc gửi lại sai lượt, mất lịch sử hoặc mở citation không đúng đoạn có thể làm người học hiểu nhầm rằng hệ thống đã ghi nhớ hay đã kiểm chứng nội dung.
- **Bài học rút ra:** Tôi học được rằng cần kiểm chứng cả happy path lẫn recovery path. Contract, owner isolation, retry và citation locator phải có test cụ thể; mock UI cũng phải được ghi nhãn rõ để không biến bằng chứng giao diện thành tuyên bố quá mức về AI thật.
