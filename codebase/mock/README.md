# Mock CP2 — VLearn Tutor: trả lời · hỏi lại · từ chối

Prototype bấm được cho luồng chính (mức **Mock**). **Chưa gọi AI thật**: mọi câu trả lời, citation và quyết định đều hardcode. AI thật làm ở CP3.

Mở `index.html` bằng trình duyệt (cần internet để tải React, Babel, Google Fonts từ CDN).

## Kịch bản
| | Thao tác | Quyết định AI |
|---|---|---|
| S1 | "Temperature là gì?" | Trả lời ngắn + citation `[Slide tr.12]`, `[T04-072]` |
| S2 | "Giải thích đoạn này" | Hỏi lại bằng lựa chọn |
| S3 | "Kill switch là gì?" | Không có trong bài → từ chối + gợi ý bước tiếp |
| S4 | "Câu 3 đáp án là gì?" | Không đưa đáp án quiz → gợi ý |
| S5 | "Chưa đúng ý" | Correction |

Nút "Kịch bản demo" (góc dưới trái) nhảy thẳng tới từng trạng thái.

Nguồn: dựng bằng Claude Design; `support.js` là runtime của file export. Số trang slide là giả; `[T04-072]` khớp transcript Day 1.
