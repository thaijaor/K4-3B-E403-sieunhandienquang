# VLearn Tutor — FE và BE ứng dụng

Gồm giao diện đọc bài, chat có citation, UI Persona và backend lưu hội thoại. Không triển khai retrieval, prompt/model hay nghiệp vụ Persona; các phần đó do nhóm AI/Persona cung cấp qua contract trong `CONTRACT.md`.

## Bố cục bài học

Sidebar trái có 3 Day, mỗi Day 2 bài Markdown mẫu tự viết trong `mock-lessons/`. Chỉ hỗ trợ H1, H2 có anchor, đoạn văn và danh sách đơn trong demo; không hiển thị Slides/Video. Citation mở đoạn gốc và đánh dấu heading trong bài. Không commit học liệu thật hoặc thư mục `data/`.

Khóa minh họa hiện gồm LLM, prompt, temperature, grounding/citation, Persona và cải thiện câu trả lời. Mỗi bài 600–900 đơn vị tách bằng khoảng trắng, có ví dụ và thực hành mở. Xem `LESSON-CONTENT.md` cho nguồn biên soạn, tương thích lịch sử và hướng dẫn chạy 12 case trong `lesson-scenarios.json`. Các case chưa phải kết quả đánh giá AI thật.

Panel AI mặc định ẩn, mở bằng “Đặt câu hỏi với AI” trên header. Đóng panel trả lại chiều ngang cho bài. Có lịch sử hội thoại trong cùng phiên, Chat mới, thu gọn và UI Persona. Trên mobile, sidebar/chat mở phủ vùng đọc và có nút đóng để quay lại bài.

## Chạy trên Windows

Từ thư mục gốc repo:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r codebase/app/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn server:create_app --factory --app-dir codebase/app --host 127.0.0.1 --port 8000
```

Mở http://127.0.0.1:8000. Mặc định dùng bài mẫu tổng hợp, không gọi AI giả. Nếu chưa cấu hình upstream, UI báo chưa kết nối. Database tự tạo tại `codebase/app/data/tutor.sqlite`, đã ignore khỏi git.

Biến môi trường (đặt trước khi chạy server):

- `AI_API_URL`: base URL dịch vụ AI; gọi `POST /respond`.
- `PERSONA_API_URL`: base URL dịch vụ Persona.
- `SERVICE_API_KEY`: bearer credential giữa BE và upstream; không đưa vào trình duyệt/git.
- `LESSONS_FILE`: đường dẫn JSON có cấu trúc như `lessons.sample.json`, dùng học liệu được cấp quyền; không commit dữ liệu khoá học.
- `TUTOR_DB`: đường dẫn database ngoài git nếu muốn đổi vị trí.
- `TUTOR_HOSTS`: host được phép, phân cách dấu phẩy; mặc định localhost/127.0.0.1/testserver.
- `COOKIE_SECURE=1`: khi chạy sau HTTPS.

Chạy **một worker**. Session ẩn danh bằng cookie HttpOnly, sống 7 ngày, tách dữ liệu giữa trình duyệt; không phải đăng nhập VLearn. Bài trong manifest đều được cấp cho tất cả session của prototype. Muốn triển khai cho lớp thật cần nối danh tính/quyền học liệu của portal, HTTPS và chính sách lưu/xoá snapshot; chưa có tích hợp VLearn thật.

## Thử UI khi chưa có dịch vụ

```powershell
.\.venv\Scripts\python.exe -m uvicorn tests.preview:create_preview --factory --app-dir codebase/app --host 127.0.0.1 --port 8765
```

Preview dùng doubles trong `tests/`, có nhãn **THỬ UI**. “Citation là gì?” thử trả lời; “Câu hỏi mơ hồ” thử hỏi lại; “quiz” thử từ chối; “Ghi nhớ ví dụ” thử proposal. Đây không phải đánh giá AI. Database preview nằm trong thư mục tạm, tạo mới mỗi lần khởi động.

## Kiểm thử

```powershell
Push-Location codebase/app
..\..\.venv\Scripts\python.exe -m unittest discover -s tests -v
Pop-Location
node --check codebase/app/static/app.js
New-Item -ItemType Directory -Force output/playwright | Out-Null
npx.cmd --yes --package @playwright/cli playwright-cli -s=tutor-app open http://127.0.0.1:8765
npx.cmd --yes --package @playwright/cli playwright-cli -s=tutor-app run-code --filename codebase/app/tests/browser-check.js
npx.cmd --yes --package @playwright/cli playwright-cli -s=tutor-app run-code --filename codebase/app/tests/layout-check.js
npx.cmd --yes --package @playwright/cli playwright-cli -s=tutor-app run-code --filename codebase/app/tests/review-check.js
```

Browser check cần preview đang chạy, chỉ xoá cookie/localStorage của browser test. Screenshot lưu tại `output/playwright/`. Bộ test dùng upstream doubles, kiểm chứng UI/BE, không chứng minh chất lượng AI hoặc dịch vụ Persona thật. Starlette hiện phát cảnh báo deprecation khi TestClient dùng httpx; test vẫn chạy.

## Hành vi và giới hạn

- Chat lưu bản text/version Persona bất biến lúc tạo. Sửa, xoá memory hoặc undo chỉ ảnh hưởng chat mới; snapshot cũ vẫn còn trong database.
- Retry giữ ID lượt phía FE, không nhân đôi. Khóa upstream được giữ khi timeout/5xx và đổi sau lỗi contract. Chỉ retry lượt cuối; lượt lỗi cũ có thể gửi thành câu hỏi mới. Một chat xử lý một lượt tại một thời điểm. Sau restart, lượt chưa xong chuyển sang lỗi để thử lại.
- BE chỉ kiểm tra citation thuộc manifest/locator, không đánh giá phát biểu có được nguồn hỗ trợ hay không.
- Nội dung AI/Persona render bằng text, không thực thi HTML. Proposal chỉ được chuyển tới API accept khi học viên bấm Lưu.
- Không có streaming, dashboard, đăng ký tài khoản, upload hay vector DB.
- Để chạy AI thật: nhóm AI/Persona cung cấp URL/credential, đáp ứng contract, đồng bộ source IDs với manifest, rồi chạy golden set riêng. Chưa có kết quả live-provider.
