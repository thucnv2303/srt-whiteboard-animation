# Project Brief — Tạo video vẽ tay

## Danh tính dự án

- Tên sản phẩm: Tạo video vẽ tay
- Repo làm việc: `thucnv2303/srt-whiteboard-animation`
- Repo upstream: `geeklee/srt-whiteboard-animation`
- Base branch: `main`
- Loại sản phẩm hiện tại: bộ công cụ Python CLI + trình chỉnh annotation chạy cục bộ trong Chrome/Edge
- Người dùng chính: người làm video tiếng Việt muốn biến nội dung SRT thành video whiteboard animation
- Môi trường ưu tiên: Windows desktop

## Vấn đề người dùng

Quy trình dựng video vẽ tay từ nội dung lời thoại đang tốn nhiều thao tác thủ công: chia cảnh, thiết kế ảnh đồng nhất, đặt thứ tự vẽ, canh thời gian, che vùng chồng lấn, render và ghép video. Người dùng cần một app dễ chạy để kiểm tra từng bước và đưa ra ý tưởng, còn Codex chịu trách nhiệm phát triển và cập nhật code.

## Kết quả sản phẩm

Từ một file SRT hợp lệ, người dùng có thể:

1. nhận đề xuất chia cảnh và chiến lược hình ảnh;
2. duyệt ảnh nét vẽ đồng nhất;
3. chỉnh vùng, thứ tự và thời gian vẽ trong giao diện;
4. render từng cảnh thành MP4;
5. ghép các cảnh thành video hoàn chỉnh;
6. nhận thông báo lỗi rõ ràng và biết cách khắc phục.

## Phạm vi MVP

- Nhập và phân tích SRT tiếng Việt.
- Chia cảnh mặc định 25–35 giây, cho phép thay đổi tham số.
- Quản lý ảnh cảnh và `annotation.json` cùng tên.
- Giao diện chỉnh region, sequence, subtitle, start/end và preview.
- Render stream whiteboard theo hai pha `ink` rồi `color`.
- Bảo vệ vùng chưa tới lượt bằng later-region masks và `protectedRegions`.
- Render MP4 từng cảnh và ghép nhiều cảnh.
- Tập trung vào trải nghiệm Windows, đường dẫn tiếng Việt và thao tác local.

## Ngoài phạm vi hiện tại

- Đăng video tự động lên TikTok/YouTube/Facebook.
- Hệ thống tài khoản, thanh toán hoặc cloud multi-user.
- Voice cloning hoặc TTS tích hợp.
- Mobile app native.
- Tự merge thay đổi vào `main` khi người dùng chưa duyệt.

## Ràng buộc sản phẩm

- Ngôn ngữ giao diện và thông báo: tiếng Việt.
- Không commit secret hoặc dữ liệu cá nhân.
- Không đưa ảnh/video của người dùng lên dịch vụ ngoài nếu chưa được cho phép.
- Mọi bước tốn chi phí hoặc thời gian render phải tuân theo cổng duyệt của người dùng.
- Giữ tương thích với định dạng annotation upstream hoặc có migration rõ ràng.

## Chỉ số thành công MVP

- Người dùng mới có thể chạy luồng mẫu theo tài liệu mà không cần sửa code.
- SRT lỗi được báo rõ, không crash mơ hồ.
- Preview và render dùng cùng một annotation làm nguồn dữ liệu.
- Video không lộ vùng chưa vẽ, đúng thứ tự kể chuyện và có đoạn giữ cuối cảnh.
- Test/smoke test có thể chạy lặp lại trước mỗi PR.
