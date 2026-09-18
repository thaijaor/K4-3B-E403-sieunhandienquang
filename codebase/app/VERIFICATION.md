# Kiểm chứng FE/BE — 18/09/2026

Nhánh local: `feat/tutor-app`, worktree `tutor-app`, base main `3d17bf8`. Không sửa mock CP2, canvas, spec hay phần teammate. Trạng thái phát hành được xác định bằng lịch sử Git của nhánh.

| Phạm vi | Bằng chứng | Kết quả |
|---|---|---|
| BE chat/session/source | `tests/test_app.py`, unittest từ thư mục app | 22 test pass |
| Persona snapshot, proxy, version conflict | Test snapshot bất biến, proposal accept/reject/undo, giới hạn text, service failure | Pass với upstream doubles |
| UI chat, nguồn, refresh | `tests/browser-check.js` qua Playwright CLI | Pass |
| UI Persona | Sửa/lưu, từ chối, sửa đề xuất/accept, undo, clear memory, conflict giữ nháp | Pass |
| Lỗi/race | Retry không nhân đôi, mất mạng giữ câu hỏi, phản hồi muộn không sang chat mới | Pass |
| Responsive và bàn phím | 320/375/1440 px không tràn ngang; drawer vừa màn; Escape trả focus | Pass |
| Tổng browser check | `output/playwright/browser-result.log` | 25 kiểm tra pass |
| Cú pháp JS | `node --check codebase/app/static/app.js` | Pass |
| Giao diện | Đã xem screenshot desktop và drawer mobile | Không phát hiện nội dung chồng/tràn ngang |

Ảnh/log nằm trong `output/playwright/`, không track git. Browser console có 409 và ERR_FAILED từ các case cố ý mô phỏng conflict/mất mạng. Unittest có cảnh báo Starlette về TestClient dùng httpx; không có test fail trong lần chạy cuối theo lệnh README.

## Bàn giao tích hợp

### Sửa lỗi chiều cao UI sau phản hồi người dùng

- Kiểm tra trước đó chỉ xét tràn ngang, nên bỏ sót nút Gửi nằm ngoài viewport. Tái hiện tại 1440 × 738: cạnh dưới nút ở y=779,9, dưới màn hình. Không dùng 25 test cũ để khẳng định toàn bộ bố cục đã đúng.
- Sửa khung desktop theo 100dvh, vùng đọc bài và tin nhắn cuộn riêng; ô nhập/header không bị vùng tin nhắn đẩy xuống. Mobile giữ panel trong một chiều cao cửa sổ khi cuộn tới chat.
- Drawer Persona có header và footer thao tác cố định, nội dung cuộn ở giữa. CSS vẫn cùng phong cách hiện tại, không nhập thêm framework/template.
- `tests/layout-check.js`: 10 viewport pass, gồm 1920×922, 1536×738, 1280×615, 1440×738, 1366×650, 1024×600, 800×500, 720×600, 375×667 và 320×568. Hai kích thước 1536×738/1280×615 mô phỏng vùng CSS tương đương zoom 125%/150% của 1920×922; không phải thao tác đổi setting Chrome thật.
- Test kiểm tra bounding rect + hit-test nút Gửi/Persona/Chat mới/ô nhập, cuộn tin nhắn dài, trạng thái banner/lỗi/đoạn chọn cùng xuất hiện, và Lưu/Huỷ/Đóng drawer với nội dung dài. 25 kiểm tra thao tác được chạy lại và pass.
- Screenshot viewport (không chụp full-page để tránh che giấu lỗi): `output/playwright/layout-chat-1536.png`, `layout-chat-320.png`, `layout-drawer-1536.png`, `layout-drawer-320.png`. Kết quả `output/playwright/layout-check.log`.

- FE và BE ứng dụng sẵn sàng theo contract tài liệu, preview đang dùng doubles có nhãn rõ.
- Chưa có URL/credential API AI/Persona thật; chưa kiểm chứng retrieval, prompt, chất lượng phản hồi, quiz guardrail, đề xuất Persona thật hoặc golden set.
- Chưa có học liệu thật được cấp cho app; citation test mở đúng đoạn bài mẫu tổng hợp, không phải chứng minh citation của dữ liệu khoá học.
- Người phụ trách AI/Persona cần đối chiếu `CONTRACT.md`, cấp API và source manifest rồi chạy nghiệm thu live. Đây là phần phụ thuộc bên ngoài, không được tính vào kết quả 22/25 ở trên.
- Prototype chạy một worker, session ẩn danh; không tuyên bố đã tích hợp đăng nhập/quyền của VLearn.
