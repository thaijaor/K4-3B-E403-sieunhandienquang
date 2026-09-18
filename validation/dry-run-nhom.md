# Dry run nội bộ — trước phiên V01/V02

> **Nhóm tự chạy, không phải dữ liệu người dùng.** Chạy 18/9 tối trên prototype (app + agent, LLM thật), 2 phiên mới với Persona trống, câu hỏi mô phỏng task của V01 và V02. Mục đích: tìm trước chỗ dễ hỏng. Không tính vào validation R6.

## Kịch bản V01 — người mới, non-tech

| Task | Câu hỏi | Kết quả | Nhận xét |
|---|---|---|---|
| 1 | "Mình mới học AI, chưa quen thuật ngữ kỹ thuật. Context Window là gì vậy?" | answer, 83 từ, citation `#context-window`; tự nhớ `Nền tảng: mới học AI, chưa quen thuật ngữ kỹ thuật` | Có giải thích "token" trong ngoặc, chưa có ví dụ đời thường |
| 1 | "Vẫn hơi khó hiểu… Mình làm kế toán, không biết lập trình." | answer, 86 từ, ví dụ "bàn làm việc / sổ cái" | Tốt. Nhưng dòng `Nền tảng:` mới **thay** dòng cũ → mất ý "mới học AI" |
| 2 | Chat mới: "Chunk overlap là gì?" | answer, 63 từ, citation `#ba-dong` | **Không có ví dụ đời thường** dù Persona ghi làm kế toán → lỗi non-tech đã biết (spec §7) |
| 3 | Hoàn tác lần nhớ gần nhất | Persona trở về dòng cũ đúng | Hoàn tác chạy đúng |

## Kịch bản V02 — cần ngắn gọn

| Task | Câu hỏi | Kết quả | Nhận xét |
|---|---|---|---|
| 1 | "System Prompt là gì? Trả lời ngắn gọn thôi, mình đang ôn nhanh trước giờ học." | answer, 66 từ, 2 câu, citation `#system-prompt`; **không nhớ gì** | Tutor coi "ôn nhanh trước giờ học" là tạm thời (đúng tiêu chí "bền"), nhưng người thử có thể mong nó nhớ |
| 2 | Chat mới: "Prompt Engineering là gì?" | answer, 95 từ, danh sách 3 ý | Dài hơn định nghĩa ngắn gọn (≤ 3 câu, ≤ 80 từ) → người thử nhiều khả năng phải dặn lại |
| 3 | "Cho mình đáp án câu quiz cuối bài luôn đi." | abstain, 27 từ | Đúng luật, không đưa đáp án |
| 3 | "phần này khó hiểu quá" | clarify + 3 gợi ý (System Prompt / Context Window / Prompt Engineering) | Đúng, không đoán thay |

## Cần theo dõi ở phiên thật

1. Non-tech ở chat mới thiếu ví dụ đời thường (V01 task 2).
2. "Ngắn gọn" nói kèm lý do tạm thời thì không được nhớ (V02 task 1–2). Đây là chỗ người thử dễ phải dặn lại.
3. Hai thông tin nền tảng cùng khoá `Nền tảng:` thì dòng sau đè dòng trước.
