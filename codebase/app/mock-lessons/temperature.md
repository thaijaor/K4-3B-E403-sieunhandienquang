# Temperature và cách sinh câu trả lời

## Mục tiêu và phạm vi {#muc-tieu}

Sau bài này, bạn có thể giải thích temperature mà không gọi nó là nút tăng trí thông minh, biết so sánh nhiều kết quả và nhận ra giới hạn của một thử nghiệm nhỏ. Bài không yêu cầu lập trình hoặc tài khoản API. Các lựa chọn và con số trong ví dụ là giả định để học, không phải kết quả đo một mô hình cụ thể.

Khi sinh văn bản, mô hình đứng trước nhiều khả năng cho token tiếp theo. Temperature là một tham số liên quan đến cách lấy mẫu từ các khả năng đó. Không phải giao diện AI nào cũng cho người dùng chỉnh tham số này; phạm vi và mặc định cần xem tài liệu của hệ thống đang dùng.

## Temperature thay đổi điều gì? {#temperature}

Nói khái quát, temperature thấp làm lựa chọn tập trung hơn vào những khả năng có xác suất cao; temperature cao làm lựa chọn phân tán hơn. Tác động xuất hiện trong quá trình chọn token, không phải bằng cách thêm tài liệu hay kiểm chứng thông tin. Cùng một yêu cầu vẫn có thể cho kết quả khác giữa các lần chạy.

Hãy tách hai câu hỏi: “Các câu trả lời giống nhau đến mức nào?” và “Các câu trả lời đúng đến mức nào?”. Một kết quả lặp lại rất ổn định vẫn có thể sai. Ngược lại, hai cách diễn đạt khác nhau có thể cùng phản ánh đúng dữ kiện. Vì vậy, độ đa dạng không thay thế tiêu chí kiểm tra nội dung.

## Ví dụ đời thường và kỹ thuật {#vi-du}

Ví dụ đời thường: một câu lạc bộ cần đặt tên cho buổi đọc sách. Bạn đưa ra yêu cầu tạo ba tên, không thêm ngày tổ chức. Những cách sinh khác nhau có thể đưa ra các tên gần gũi hoặc bất ngờ hơn. Dù tên thú vị đến đâu, nếu kết quả tự thêm thời gian hoặc hứa tặng quà, nó vẫn vi phạm dữ kiện đã cho.

Ví dụ kỹ thuật: một ứng dụng cần phân loại lời nhắn thành “hỏi thông tin” hoặc “báo lỗi”. Bạn muốn đầu ra theo nhãn cố định. Thử temperature khác nhau có thể giúp khảo sát tính ổn định, nhưng không đủ chứng minh chất lượng bộ phân loại. Cần những lời nhắn đã được người đánh giá gán nhãn và kiểm tra các trường hợp khó, chẳng hạn một lời nhắn vừa hỏi vừa báo lỗi.

Hai ví dụ có mục tiêu khác nhau. Với tên sự kiện, nhiều phương án có ích. Với phân loại, đầu ra phải nhất quán với quy tắc. Không nên lấy một cấu hình thành công ở nhiệm vụ đầu rồi khẳng định nó tối ưu cho nhiệm vụ thứ hai.

## Thử nghiệm công bằng {#thu-nghiem}

Muốn quan sát tác động của một thay đổi, hãy giữ các điều kiện còn lại giống nhau: mô hình, câu hỏi, đoạn nguồn và cách chấm. Chạy nhiều lượt cho mỗi cấu hình nếu hệ thống cho phép, lưu cả kết quả tốt lẫn lỗi. Khi đồng thời đổi prompt và mô hình, bạn không thể quy toàn bộ khác biệt cho temperature.

- Viết trước điều gì được coi là đạt: đủ ba tên, không bịa dữ kiện hoặc dùng đúng nhãn.
- Ghi lại cấu hình thực sự sử dụng; không đoán tham số của một ứng dụng chỉ từ văn phong.
- Đếm số lượt đạt theo cùng một cách, đồng thời đọc các trường hợp không đạt.
- Kết luận trong phạm vi mẫu đã thử, không biến vài lượt thành cam kết cho mọi người dùng.

Nếu giao diện Tutor không cung cấp nút chỉnh temperature, bạn vẫn có thể làm bài bằng các kết quả giả định đã tự viết và so sánh tiêu chí. Không gắn nhãn các kết quả đó là dữ liệu thực nghiệm của mô hình.

## Hiểu lầm và giới hạn {#hieu-lam}

Temperature bằng không không phải chứng nhận sự thật, cũng không nên được quảng cáo là lời hứa giống nhau từng chữ trong mọi hệ thống. Kết quả còn phụ thuộc cách triển khai và những điều kiện khác. Bài này không đưa ra một giá trị tối ưu áp dụng chung.

Yêu cầu “ngắn hơn” trong Persona là sở thích trình bày, không đồng nghĩa ứng dụng đã thay đổi temperature. Hạ temperature cũng không tự giải quyết thiếu nguồn. Nếu bài đang mở không có thông tin để trả lời, Tutor vẫn cần hỏi lại hoặc nói rõ giới hạn, thay vì sinh một kết luận ổn định nhưng vô căn cứ.

## Thực hành, tóm tắt và câu hỏi {#thuc-hanh}

Tạo ba câu trả lời giả định cho yêu cầu đặt tên sự kiện: một câu đúng mọi điều kiện, một câu thêm ngày tổ chức, một câu chỉ có hai tên. Viết tiêu chí đánh giá rồi tự chấm bằng cách chỉ vào chi tiết cụ thể. Không cần chọn một “đáp án hay nhất” nếu các tiêu chí chưa đủ rõ.

Tóm tắt: temperature ảnh hưởng cách chọn khả năng, còn chất lượng cần kiểm tra theo nhiệm vụ và nguồn. Hãy thử hỏi Tutor:

- Vì sao temperature thấp không bảo đảm câu trả lời đúng?
- Thiết kế một thử nghiệm nhỏ mà chỉ đổi một điều kiện như thế nào?
- Sở thích “ngắn gọn” trong Persona khác gì tham số temperature?
