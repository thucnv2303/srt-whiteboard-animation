# Gói kiểm thử 52 giây

Gói này dùng sáu cảnh, mỗi cảnh `8.6` giây, tổng thời lượng dự kiến khoảng `51.6` giây.

Mục tiêu là kiểm tra kỹ thuật:

- app đọc được dự án nhiều cảnh;
- renderer tạo từng MP4 cảnh;
- app ghép đúng thứ tự thành `final.mp4`;
- UI vẫn phản hồi và ghi log trong lúc render.

Đây là fixture kỹ thuật nên sáu cảnh cố ý dùng lại cùng một ảnh và annotation. Gói chưa có voice. Sau khi luồng này đạt trên Windows, dự án mẫu nội dung thật sẽ dùng ảnh và voice riêng cho từng cảnh.

