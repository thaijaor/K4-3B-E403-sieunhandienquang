# Viết prompt rõ ràng

## Mục tiêu và tình huống học {#muc-tieu}

Sau bài này, bạn có thể viết một yêu cầu có mục tiêu, ngữ cảnh, giới hạn và hình thức đầu ra. Bạn cũng biết nhận ra khi cần hỏi lại thay vì tiếp tục đoán. Không cần sử dụng một cấu trúc câu thần kỳ: một prompt tốt trước hết giúp người đọc hiểu bạn muốn đạt điều gì và được phép dựa vào thông tin nào.

Chúng ta dùng tình huống tự viết thông báo cho một câu lạc bộ. Mọi tên gọi và dữ liệu trong ví dụ đều là giả định phục vụ thực hành. Với hệ thống Tutor, đoạn bài đang mở mới là nguồn trả lời; viết prompt rõ không mở rộng quyền truy cập sang học liệu khác.

## Bốn thành phần của yêu cầu {#bon-thanh-phan}

- Mục tiêu: mô tả việc cần làm, chẳng hạn tóm tắt, so sánh hoặc giải thích một khái niệm.
- Ngữ cảnh: cung cấp thông tin cần thiết và người sẽ đọc kết quả, thay vì yêu cầu mô hình tự đoán hoàn cảnh.
- Ràng buộc: nêu giới hạn nguồn, điều không được tự thêm và những điểm phải giữ lại.
- Đầu ra: chỉ rõ độ dài hoặc cấu trúc cần dùng, chẳng hạn một đoạn văn hay ba gạch đầu dòng.

Không phải mọi câu hỏi đều cần viết đủ bốn nhãn. Nếu bạn đã chọn một đoạn trong bài, “Giải thích khái niệm này bằng một ví dụ dễ hiểu” có thể đủ. Nhưng khi yêu cầu nhiều bước, việc tách các thành phần giúp bạn phát hiện thông tin còn thiếu trước khi gửi.

## So sánh yêu cầu thiếu và đủ thông tin {#so-sanh}

Yêu cầu thiếu thông tin: “Viết thông báo hay hơn”. Chưa rõ thông báo nào, gửi cho ai, thay đổi phần nào và cần giữ sự kiện gì. Nếu không có đoạn gốc, một câu hỏi làm rõ là hữu ích hơn việc tự tạo ngày giờ.

Yêu cầu rõ hơn: “Dựa vào ghi chú sau, viết thông báo ba câu cho thành viên mới. Giữ nguyên thời gian và địa điểm; không thêm lệ phí. Ghi chú: buổi đọc sách diễn ra lúc 9 giờ sáng thứ Bảy tại phòng B, người tham gia mang một cuốn sách”. Người kiểm tra có thể đối chiếu đầu ra với từng điều kiện mà không cần đoán ý tác giả.

Ví dụ này không bảo đảm mô hình luôn tuân thủ. Nó tạo ra các tiêu chí dễ kiểm tra. Nếu đầu ra tự thêm “vé vào cửa miễn phí”, bạn vẫn phải xem ghi chú có xác nhận miễn phí hay chỉ chưa đề cập đến lệ phí. Thiếu thông tin không tương đương một khẳng định phủ định.

## Ví dụ kỹ thuật không cần chạy mã {#vi-du-ky-thuat}

Giả sử ghi chú của một chức năng là “Nhập tên, nhấn Lưu, hệ thống báo đã lưu”. Bạn muốn lập danh sách trường hợp kiểm tra. Có thể yêu cầu: “Từ mô tả này, liệt kê ba điều cần hỏi người thiết kế trước khi viết test. Không tự quyết định giới hạn độ dài hoặc cách xử lý tên rỗng”.

Đầu ra hữu ích ở đây là làm lộ các quyết định còn thiếu, không phải một bộ quy tắc do AI tự tạo. Người đã biết lập trình có thể yêu cầu trình bày dưới dạng các bước kiểm tra; người mới có thể yêu cầu ví dụ thao tác bằng chuột. Nhu cầu trình bày thay đổi nhưng dữ kiện gốc vẫn phải giữ nguyên.

## Làm rõ và sửa từng bước {#lam-ro}

Khi kết quả chưa đúng ý, hãy xác định vấn đề cụ thể: thiếu thông tin, sai phạm vi, quá dài hay dùng thuật ngữ khó hiểu. “Ngắn hơn nhưng giữ nguyên ba điều kiện” dễ kiểm tra hơn “làm tốt hơn”. Nếu vấn đề là thiếu nguồn, đổi giọng văn không sửa được vấn đề đó.

Một quy trình nhỏ là đọc kết quả, chọn một lỗi quan trọng, yêu cầu chỉnh đúng lỗi đó rồi đối chiếu lại. Không thay đồng thời nhiều điều kiện nếu bạn muốn biết thay đổi nào có tác dụng. Trong Tutor, có thể dùng Persona để giữ sở thích cách trình bày; không cần nhắc lại mọi sở thích trong từng câu hỏi.

## Hiểu lầm, thực hành và tóm tắt {#thuc-hanh}

Prompt dài không tự động tốt hơn; thông tin liên quan mới quan trọng. Việc yêu cầu AI đóng vai chuyên gia không biến câu trả lời thành bằng chứng chuyên môn. Một ví dụ đầu ra cũng không cho phép bỏ qua giới hạn nguồn hoặc tự tạo dữ kiện.

Thực hành: viết một yêu cầu mơ hồ về việc tóm tắt ghi chú câu lạc bộ, sau đó sửa bằng bốn thành phần đã học. Nhờ một người khác đọc và chỉ ra điều họ vẫn phải đoán. Không cần lấy đáp án có sẵn; sản phẩm cần nộp là hai phiên bản prompt và lý do của từng thay đổi.

- Vì sao “không đề cập lệ phí” khác với “miễn phí”?
- Khi nào Tutor nên hỏi lại trước khi trả lời?
- Hãy chỉ ra mục tiêu, ngữ cảnh và ràng buộc trong ví dụ thông báo.
