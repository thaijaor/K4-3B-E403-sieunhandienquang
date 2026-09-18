# Thu Hoạch Cá Nhân — Nguyễn Hồng Thái

- **Họ và tên:** Nguyễn Hồng Thái
- **Mã học viên (MSSV):** `2A202602894`
- **Lớp:** 3B · **Phòng:** E403
- **Nhóm:** sieunhandienquang · **Track:** A1 — Tối ưu AI Tutor VLearn hiện có

---

## 1. Vai trò cá nhân trong nhóm

Trong dự án **Tutor nhớ cách trả lời học viên muốn (Persona)**, tôi đảm nhiệm vai trò **đội trưởng + Product/Spec/Persona**, phụ trách quyết định sản phẩm, đặc tả Persona, quality bar và điều phối bài nộp.

- **Product + Spec:** tổng hợp evidence do nhóm thu thập, lập bảng impact và chốt lát cắt Persona làm trọng tâm.
- **Persona:** xây luồng Tutor tự ghi nhớ/quên, hoàn tác và các giới hạn không ghi điều nhạy cảm hoặc nội dung chỉ xuất hiện trong bài học.
- **Eval + Delivery:** mở rộng golden set lên 39 case, chốt quality bar, tổng hợp các lượt đo và phân tích case trượt trong [spec.md](../spec.md) và [eval/](../eval/).

---

## 2. Phần việc trực tiếp phụ trách

1. **Chuyển evidence của nhóm thành quyết định sản phẩm**

   - Tổng hợp số liệu chatlog và kết quả khảo sát do nhóm thu thập: 172 lượt của 95 học viên K4 yêu cầu đổi cách trả lời; 15/20 học viên khảo sát xác nhận pain.
   - Chuyển Persona từ phần mở rộng thành lát cắt chính, đồng thời giữ citation và guardrail là điều kiện bắt buộc.

2. **Thiết kế và tích hợp Persona**

   - Xây cơ chế tự ghi nhớ theo bốn tiêu chí, cho phép quên và hoàn tác, đồng thời chặn ghi nhớ định dạng trái luật hoặc thông tin nhạy cảm.
   - Phối hợp contract giữa agent và ứng dụng để Persona được áp dụng từ câu hỏi tiếp theo và còn hiệu lực ở chat mới.
   - Các thay đổi chính được thể hiện trong commit `bb45c42`, `6db4dd5` và các test Persona liên quan.

3. **Chốt cách đo và báo cáo trung thực**

   - Chuyển bộ đo từ 20 case lõi sang 39 case tập trung vào ghi nhớ, tuân theo Persona, không phá luật, số lần dặn lại và chất lượng lõi.
   - Chốt quality bar trước hạn CP4, chạy đủ case, kết hợp chấm tự động và chấm tay, không hạ bar khi kết quả chưa đạt.
   - Ghi rõ lượt 2 đạt 5/8 chỉ số và phân tích ba khoảng cách còn lại trong [eval/eval_report_run2.md](../eval/eval_report_run2.md).

---

## 3. Cách thức ứng dụng AI trong quá trình xây dựng

Tôi dùng AI để hỗ trợ đọc cấu trúc code, đề xuất test case, sửa prompt và tổng hợp báo cáo eval. AI giúp tăng tốc triển khai nhưng kết quả không được coi là đúng nếu chưa đối chiếu với trace, nhãn golden set và người chấm.

1. Các thay đổi Persona được kiểm tra lại bằng unit test và lượt chạy end-to-end, không chỉ dựa trên code AI sinh ra.
2. Điểm do LLM-as-judge được lưu riêng và ghi rõ không phải điểm người chấm; kết quả chính dùng phần chấm tay đã được Thái và Cường đối chiếu.
3. Evidence, quote khảo sát và kết quả case trượt được giữ nguyên theo dữ liệu; AI không được tạo thêm phản hồi hoặc làm đẹp số liệu.

---

## 4. Một bài học thực tế rút ra từ chính các trường hợp thất bại của nhóm

### 🔴 Hành vi hợp lý của model vẫn có thể trượt tiêu chí đã chốt

- **Sự cố/giới hạn:** Ở case A12, học viên yêu cầu quên việc mình là người mới và nói rằng giờ đã quen AI. Tutor xóa dòng cũ nhưng đồng thời ghi thêm “Nền tảng: đã quen với AI”, trong khi nhãn chỉ chấp nhận thao tác quên. Lượt 2 vì vậy chỉ đạt precision ghi nhớ 83%; phần non-tech cũng còn lọt thuật ngữ và thiếu ví dụ đời thường.
- **Phân tích:** Câu trả lời nghe hợp lý chưa đủ để chứng minh hệ thống tuân theo contract. Với bộ nhớ người dùng, mỗi thao tác ghi thêm đều cần căn cứ rõ ràng; với Persona non-tech, “đổi giọng” không đồng nghĩa mọi thuật ngữ đã được giải thích.
- **Bài học rút ra:** Tôi học được rằng quality bar phải mô tả hành vi đủ cụ thể và được giữ nguyên sau khi chốt. Khi kết quả chưa đạt, cách đúng là công khai khoảng cách, truy về case cụ thể và sửa hệ thống, không thay nhãn hoặc hạ bar để có số đẹp.
