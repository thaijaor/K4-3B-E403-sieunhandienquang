# LLM hoạt động như thế nào?

## Mục tiêu và điểm xuất phát {#muc-tieu}

Sau bài này, bạn có thể giải thích token bằng ngôn ngữ của mình, mô tả cách một mô hình sinh văn bản và phân biệt câu trả lời dễ đọc với câu trả lời có bằng chứng. Bạn không cần biết lập trình. Hãy chuẩn bị một đoạn văn ngắn do chính bạn viết để làm thực hành; không dùng hồ sơ khách hàng hoặc thông tin cá nhân nhạy cảm.

LLM là viết tắt của mô hình ngôn ngữ lớn. Trong bài này, chúng ta tập trung vào mô hình sinh văn bản nối tiếp: nhận ngữ cảnh rồi tạo phần tiếp theo. Đây là mô tả khái quát để học cách sử dụng, không phải mô tả đầy đủ mọi kiến trúc hay sản phẩm AI.

## Token là đơn vị xử lý văn bản {#token}

Trước khi xử lý, văn bản được chuyển thành các đơn vị gọi là token. Một token có thể tương ứng với một từ, một phần của từ hoặc dấu câu. Vì vậy, không nên hiểu “một trăm token” là “một trăm từ”. Cách chia phụ thuộc bộ tách token của mô hình và ngôn ngữ được sử dụng.

Hãy hình dung bạn xếp một câu bằng các mảnh ghép. Mảnh ghép giúp máy biểu diễn văn bản, nhưng ranh giới mảnh không nhất thiết trùng ranh giới ý nghĩa mà người đọc nhận thấy. Ví dụ minh họa “học máy” có hai từ khi nhìn bằng mắt; bài này không khẳng định nó luôn có hai token trong mọi hệ thống.

## Từ ngữ cảnh đến câu trả lời {#sinh-van-ban}

Mô hình sử dụng ngữ cảnh để tính các khả năng cho token tiếp theo. Một cách chọn token được áp dụng, token được thêm vào chuỗi, rồi quá trình tiếp tục. Kết quả dài được hình thành qua nhiều bước như vậy. Ngữ cảnh có thể gồm câu hỏi, các lượt trao đổi trước và đoạn tài liệu mà ứng dụng cung cấp.

Trong giai đoạn huấn luyện, mô hình đã học các mẫu thống kê từ dữ liệu. Khi bạn gửi một câu hỏi thông thường, việc sinh câu trả lời không đồng nghĩa mô hình vừa được huấn luyện lại. Cũng không nên mặc định rằng mọi câu hỏi đều khiến ứng dụng tự tìm trên Internet: tìm kiếm là khả năng do sản phẩm tổ chức, không phải điều được đảm bảo chỉ vì có LLM.

## Hai ví dụ để tự giải thích {#vi-du}

Ví dụ đời thường: bạn viết “Hôm nay trời mưa, tôi mang theo…”. Người đọc có thể nghĩ đến ô hoặc áo mưa. Ngữ cảnh làm một số cách tiếp nối hợp lý hơn các cách khác. Tuy nhiên, câu được nối hợp lý không chứng minh hôm nay thực sự có mưa. Một mô tả nghe tự nhiên và một sự kiện ngoài đời là hai thứ cần phân biệt.

Ví dụ kỹ thuật: đưa cho Tutor đoạn ghi chú “Ứng dụng lưu bản nháp mỗi phút” rồi yêu cầu tóm tắt. Một câu trả lời phù hợp giữ lại ý lưu bản nháp. Nếu nó thêm “dữ liệu luôn được đồng bộ lên máy chủ”, bạn phải tìm căn cứ cho phần thêm đó. Khả năng viết câu hoàn chỉnh không cấp cho mô hình quyền bổ sung đặc tính chưa được cung cấp.

## Giới hạn và hiểu lầm thường gặp {#gioi-han}

- Văn phong tự tin không phải phép đo độ đúng. Hãy kiểm tra các khẳng định quan trọng bằng nguồn phù hợp.
- Ngữ cảnh dài hơn không tự đảm bảo câu trả lời tốt hơn. Nội dung không liên quan có thể làm việc kiểm tra khó hơn.
- Mô hình trả lời khác nhau không nhất thiết có nghĩa nó vừa học điều mới từ bạn. Cách sinh và ngữ cảnh có thể khác.
- Không suy từ một ví dụ trả lời đúng rằng hệ thống sẽ đúng trong mọi tình huống tương tự.

Với Tutor của prototype này, câu trả lời cần dựa vào bài đang mở. Đó là quy tắc của ứng dụng. Nếu bạn hỏi một kiến thức không được trình bày trong bài, hành vi phù hợp là nhận giới hạn nguồn, không bù khoảng trống bằng một câu nghe có vẻ hợp lý.

## Thực hành và tự kiểm tra {#thuc-hanh}

Viết ba câu mô tả một cửa hàng tưởng tượng, gồm giờ mở cửa, mặt hàng và một quy định đổi hàng. Nhờ Tutor tóm tắt rồi đánh dấu từng ý là “có trong đoạn” hoặc “chưa có căn cứ”. Không cần câu trả lời mẫu: mục tiêu là bạn tự chứng minh được nguồn của từng ý.

Tóm tắt: token là đơn vị biểu diễn, ngữ cảnh ảnh hưởng phần được sinh, còn độ đúng cần kiểm chứng. Sau khi đọc, hãy thử hỏi:

- Token có luôn bằng một từ không? Giải thích bằng ví dụ đời thường.
- Việc trả lời câu hỏi khác gì việc huấn luyện mô hình?
- Vì sao câu nối tiếp hợp lý vẫn có thể chứa thông tin sai?
