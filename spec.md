# Template AI Spec *(spec.md — commit trước hạn chốt spec: 21:00 18/9, tại CP4 · quality bar chốt từ thời điểm nộp)*

## Bổ sung triển khai học liệu — 18/09/2026

Phần này bổ sung cho §4 và §9 của bản spec Persona tại PR #5 (đối chiếu commit `f40e3ab2a521ef95cbad421882a3c5cc668d2460`), không thay thế evidence, quality bar, phân công hoặc canvas CP1. Template phía dưới được giữ nguyên để không ghi đè phần teammate đang cập nhật.

- Theo feedback “cho mấy cái này có bài học đàng hoàng”, prototype cung cấp 6 bài AI/LLM cơ bản tự biên soạn: LLM, prompt, temperature, grounding/citation, Persona, kiểm tra và cải thiện câu trả lời; bố cục 3 ngày × 2 bài.
- Mỗi bài có mục tiêu, giải thích, ví dụ đời thường/kỹ thuật, giới hạn, thực hành mở và câu hỏi; H2 có anchor ổn định cho citation. Nhãn học liệu minh họa được giữ, không nhận là nội dung VLearn chính thức.
- Persona vẫn là trọng tâm trải nghiệm: cùng câu hỏi và nguồn, thay đổi cách giải thích theo snapshot của chat. Luật nguồn và không đưa đáp án quiz không bị Persona ghi đè. Không triển khai thêm service AI/Persona trong thay đổi này.
- Thêm 12 kịch bản bổ sung tại `codebase/app/lesson-scenarios.json`, hướng dẫn và nguồn đối chiếu tại `codebase/app/LESSON-CONTENT.md`. Không thay golden set hoặc tự chốt quality bar. Kiểm thử UI bằng doubles không được ghi là đánh giá chất lượng AI thật.

| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| 18/09/2026 | Thay nội dung ngắn bằng 6 bài AI/LLM có ví dụ, thực hành, nguồn nội bộ và 12 case Persona | Feedback cần học liệu đầy đủ để người dùng thực sự đọc bài và hỏi Tutor; giữ hướng Persona và citation của PR #5 |


> Cấu trúc phủ đúng "SPEC 8 phần" của chương trình: Bằng chứng (§1-§2) · Lát cắt (§4) · Canvas (đính kèm CP1) · Augment/Automate (§4) · 4 đường đi của trải nghiệm (§6) · Kiểu lỗi (§5) · Kiểm thử (§7) · Phân công (§8). Hướng dẫn viết từng mục: `02-guide.md`.

```markdown
# AI SPEC — [Tên lát cắt] · Nhóm [XX] · Zone [X]
Hướng: [ ] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [ ] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job
- Job executor + workflow (đính kèm worksheet JTBD / ảnh sơ đồ):
- Core JTBD (không tên sản phẩm/AI trong câu):
- Problem statement (KHÔNG chữ AI):
- Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):
  - Số liệu mining / kết quả khảo sát (n = ?, % xác nhận):
  - ≥5 quote/ví dụ nguyên văn + nguồn:

## §2. Impact & quyết định chọn
- Bảng impact ≥3 ứng viên (bao nhiêu người · tần suất · tốn gì mỗi lần · khả thi):
- Ứng viên ĐÃ LOẠI + vì sao:
- Ứng viên CHỌN + vì sao (bằng số):

## §3. Giải pháp tương tự đã nghiên cứu
- [Sản phẩm 1]: flow / đáng học / đáng né / mình khác gì
- [Sản phẩm 2]: ...

## §4. Thiết kế
- Lát cắt MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả):
- Non-goals (≥3 thứ KHÔNG build):
- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [ ] Working — phần nào mock, phần nào thật:
- Automation: [ ] augment [ ] conditional [ ] automate — lý do theo cost-of-error:
- §4b. Nguyên tắc đã áp dụng (≥4 — HAX/PAIR, xem guide):
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8) [bảng theo guide §2.5]

## §6. Bốn đường đi của trải nghiệm
- Happy path: · Low-confidence (②): · Failure/không căn cứ (①): · Correction (user sửa):
- Khi bị đòi ngoài phạm vi (③): · Case đặc thù domain (④):

## §7. Kiểm thử
- Chiều chất lượng + định nghĩa kiểm chứng được:
- Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/):
- Quality bar (chốt từ hạn chốt spec của khoá, giữ nguyên sau đó): "Đạt khi ≥ ___% qua bộ, và ___"
- Kết quả các lượt chạy (bảng % — cập nhật đến trước CP6):

## §8. Phân công & kế hoạch
- Phân công có tên: spec / evidence / prompt / code / demo
- Willing users (≥2 tên) + kế hoạch vòng validation *(bonus, nếu làm)*:
- Multi-prototype (nếu làm): trục khác biệt của ≥2 phương án + lý do chọn:

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
```
