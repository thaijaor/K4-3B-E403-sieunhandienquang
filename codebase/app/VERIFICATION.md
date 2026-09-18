# Kiểm chứng FE/BE — cập nhật review PR #4, 18/09/2026

Nhánh `feat/tutor-app`, worktree `tutor-app`. Chỉ sửa `codebase/app/`; không sửa canvas, spec, mock CP2 hay triển khai AI/Persona service của teammate.

| Phạm vi | Bằng chứng hiện tại | Kết quả |
|---|---|---|
| Backend | `tests/test_app.py`, unittest từ thư mục app | 31 test pass |
| Retry và exception | Khóa đổi sau lỗi contract/JSON, khóa giữ sau timeout, khóa mới tồn tại qua restart, không retry lượt cũ, lỗi bất ngờ và SQLite khóa cả lúc hoàn tất/lúc dọn | Pass với lỗi chủ động chèn |
| Danh sách chat | Owner isolation, thứ tự mới nhất trước | Pass |
| Markdown | 6 bài, 3 Day, IDs duy nhất, nguồn/locator khớp file và anchor, preview trả citation hợp lệ ở mọi bài | Pass |
| Chat và Persona UI | `tests/browser-check.js`: refresh, sửa Persona, ghi nhớ tự động + hoàn tác, clear, network retry, phản hồi muộn, drawer và focus | 23 kiểm tra pass |
| Yêu cầu UI trong review | `tests/review-check.js`: ẩn/mở/đóng/thu gọn chat, vùng đọc mở rộng, sidebar/accordion/active label, 6 bài và citation, lịch sử chat, mobile | 43 kiểm tra pass |
| Bố cục | `tests/layout-check.js`: bounding rect + hit-test và cuộn thực | 10 viewport pass |
| Cú pháp | `node --check codebase/app/static/app.js`, Python compileall, `git diff --check` | Pass |

## Kiểm tra trực quan

Đã xem ảnh viewport desktop có/không có chat, mobile 320px và Persona drawer. Header panel có nút đóng ở góc phải; ô nhập và Gửi nằm trong viewport. Vùng đọc/tin nhắn cuộn riêng. Mobile mở chat phủ vùng đọc, đóng để trở lại bài.

10 viewport: 1920×922, 1536×738, 1280×615, 1440×738, 1366×650, 1024×600, 800×500, 720×600, 375×667, 320×568. Test kiểm tra Gửi/Persona/Chat mới/Lịch sử/Thu gọn/Đóng/ô nhập bằng bounding rect và hit-test, khi banner/lỗi/đoạn chọn cùng xuất hiện; cũng kiểm tra Lưu/Huỷ/Đóng drawer với nội dung dài. Dung sai hình học 1px để tính sai số subpixel; không bỏ kiểm tra overflow.

Ảnh/log tại `output/playwright/`, không track git: `review-reading-desktop.png`, `review-chat-desktop.png`, `review-chat-mobile.png`, `layout-chat-1536.png`, `layout-chat-320.png`, `layout-drawer-1536.png`, `layout-drawer-320.png`. Script lưu kết quả vào `window.__browserCheck`, `window.__reviewCheck`, `window.__layoutCheck`; đọc các biến này sau khi run-code để xác nhận hoàn tất, vì CLI có thể trả sớm khi gặp confirm dialog.

Console ERR_FAILED trong browser check là lỗi cố ý mô phỏng mất mạng. Traceback KeyError/RuntimeError/SQLite locked trong unittest là lỗi chèn để kiểm tra recovery. Starlette có cảnh báo deprecation TestClient/httpx; không có test fail trong lần chạy cuối.

## Ranh giới bằng chứng

- Toàn bộ AI/Persona trong preview là doubles có nhãn THỬ UI. Không có kết quả live-provider, retrieval, prompt, quiz guardrail hoặc golden set.
- 6 file trong `mock-lessons/` là bài tự viết; không dùng hoặc commit học liệu thật, `data/`, database hay credential.
- Demo Markdown hỗ trợ heading, đoạn văn và danh sách đơn. Citation mở đúng đoạn của bài mẫu, không chứng minh tính đúng đắn của phát biểu AI.
- AI/Persona owner cần đối chiếu `CONTRACT.md`, nhất là khóa retry và source ID/locator mới, trước khi nối live.
- Một worker, cookie session ẩn danh; chưa tích hợp đăng nhập/quyền học liệu VLearn. Lịch sử thuộc phiên cookie hiện tại.
