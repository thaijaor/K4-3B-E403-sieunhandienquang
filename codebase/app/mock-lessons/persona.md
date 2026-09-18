# Persona trong trợ giảng AI

## Mục tiêu và nhu cầu người học {#muc-tieu}

Sau bài này, bạn có thể viết một Persona ngắn, phân biệt sở thích trình bày với dữ kiện và giải thích vì sao việc ghi nhớ cần sự đồng ý. Những quy tắc về lưu và áp dụng Persona dưới đây mô tả thiết kế của prototype Tutor trong dự án này, không phải hành vi mặc định của mọi sản phẩm AI.

Hai người học có thể hỏi cùng một khái niệm nhưng cần cách giải thích khác nhau. Người mới muốn ví dụ gần gũi, người đã có nền tảng kỹ thuật muốn thuật ngữ chính xác và các bước. Persona giúp mô tả nhu cầu đó để người học không phải lặp lại sở thích ở mọi cuộc trao đổi.

## Ba phần của Persona {#ba-phan}

- Tính cách Tutor: người học chọn cách xưng hô, mức chi tiết và kiểu giải thích mong muốn.
- Tutor nhớ về bạn: thông tin phục vụ việc học mà Tutor đề xuất ghi và người học đồng ý lưu.
- Không được nhớ: những nội dung người học không muốn đưa vào phần ghi nhớ.

Văn bản Persona được giới hạn tối đa 2.000 ký tự theo thiết kế hiện tại. Hãy ưu tiên điều ảnh hưởng trực tiếp đến việc giải thích, chẳng hạn “Tôi chưa học lập trình; giải thích thuật ngữ trước khi dùng”. Không cần ghi tên thật, địa chỉ, số điện thoại hoặc tài khoản để mô tả nhu cầu này.

Một Persona hữu ích không phải hồ sơ càng dài càng tốt. Nếu bạn ghi những sở thích mâu thuẫn như “chỉ một câu” và “luôn giải thích đủ mọi bước”, Tutor có thể cần làm rõ. Bạn cũng nên sửa lại sở thích khi kiến thức hoặc mục tiêu học thay đổi.

## Ví dụ đời thường và kỹ thuật {#vi-du}

Ví dụ đời thường: “Xưng hô mình–bạn, giải thích bằng ví dụ câu lạc bộ hoặc cửa hàng; dùng ít thuật ngữ”. Với cùng một bài, người học có thể dễ liên hệ các điều kiện trừu tượng với hoạt động đã biết. Ví dụ chỉ có nhiệm vụ minh họa, không được mang thêm quy định mới ngoài nguồn.

Ví dụ kỹ thuật: “Tôi hiểu khái niệm đầu vào và đầu ra; trình bày theo bước, nêu điều kiện và trường hợp lỗi”. Tutor có thể dùng cách tổ chức này thay cho một đoạn văn dài. Người đọc vẫn phải đối chiếu citation; việc dùng thuật ngữ chuyên môn không làm bằng chứng mạnh hơn.

Để so sánh công bằng, giữ nguyên câu hỏi và bài học, chỉ đổi Persona trong chat mới. Nếu cả câu hỏi lẫn nguồn đều thay đổi, bạn khó biết khác biệt đến từ sở thích hay từ thông tin được cung cấp. Đây là một cách thử hành vi, không phải phép đo năng lực tổng quát của AI.

## Lưu có xác nhận và áp dụng từ chat mới {#snapshot}

Khi tạo chat, ứng dụng lấy một bản Persona tại thời điểm đó làm snapshot. Sửa Persona sau đó chỉ áp dụng cho chat mới, không âm thầm đổi cách hiểu lịch sử đang mở. Bạn có thể xem phiên bản đang dùng để biết vì sao hai cuộc trò chuyện không nhất thiết có cùng cách trình bày.

Nếu Tutor đề xuất ghi nhớ “ưu tiên ví dụ dễ hiểu”, người học cần xem phần thay đổi trước khi chọn Lưu, Sửa hoặc Không. Chọn Không phải giữ nguyên Persona. Sau khi lưu, có thể dùng Hoàn tác nếu thay đổi không đúng ý; các chat đã tạo vẫn giữ snapshot cũ theo thiết kế.

Xóa phần ghi nhớ hiện tại cũng không đồng nghĩa tự động xóa toàn bộ snapshot trong lịch sử. Đừng nhập dữ liệu nhạy cảm chỉ vì nghĩ có thể xóa sạch bằng một nút. Cơ chế lưu trữ lịch sử và chính sách xóa dữ liệu là vấn đề riêng cần được giải thích rõ khi triển khai cho người dùng thật.

## Sở thích không thay đổi quy tắc {#gioi-han}

Persona không được cấp quyền đưa đáp án quiz, bịa citation hoặc trả lời từ nguồn ngoài bài. Nếu một Persona yêu cầu “luôn đồng ý với tôi”, Tutor vẫn cần giữ ràng buộc nguồn. Dữ liệu mô tả sở thích không được dùng để ghi đè luật cố định của hệ thống.

“Ngắn gọn” cũng không có nghĩa cắt bỏ điều kiện quan trọng. Với một quy trình nhiều bước, câu trả lời ngắn vẫn phải giữ những bước cần thiết. Khi cần, Tutor có thể nói rõ giới hạn của việc rút gọn thay vì đưa lời giải thiếu điều kiện.

## Thực hành và tự kiểm tra {#thuc-hanh}

Viết một Persona ba dòng không chứa thông tin định danh. Dùng một câu hỏi trong bài để thử, sửa mức chi tiết, rồi tạo chat mới. Ghi lại phiên bản và kiểm tra xem chat cũ có giữ snapshot hay không. Nếu service chưa kết nối, chỉ kiểm tra được giao diện hoặc test giả lập; không kết luận chất lượng AI thật.

Tóm tắt: Persona là sở thích có kiểm soát, không phải nguồn sự thật hay quyền vượt rào. Hãy hỏi tiếp:

- Vì sao sửa Persona chỉ áp dụng từ chat mới?
- Tutor nên làm gì khi người học từ chối đề xuất ghi nhớ?
- “Ngắn gọn” có cho phép bỏ bước quan trọng hoặc bỏ citation không?
