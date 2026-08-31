# Luồng sản phẩm và cổng duyệt

## Nguyên tắc

Codex xây dựng và sửa app. Người dùng vận hành app, xem kết quả trực quan và quyết định có chuyển bước hay cần sửa. Không coi sự im lặng là đồng ý.

## Luồng chuẩn

### Bước 1 — Nhập SRT và chia cảnh

- Input: file `.srt` UTF-8/UTF-8 BOM.
- Hệ thống trả danh sách cue, thời lượng và gợi ý cảnh.
- Mỗi cảnh mặc định 25–35 giây và chỉ diễn đạt một ý chính.
- Dừng để người dùng duyệt nội dung, thứ tự và thời lượng cảnh.

### Bước 2 — Chuẩn bị ảnh nét vẽ

- Chỉ bắt đầu sau khi người dùng duyệt bước 1.
- Ảnh 16:9, nền `#F5EBD7`, nét xám đậm, ít đỏ/cam/xanh làm điểm nhấn.
- Không có chữ, số, nhãn, nền phức tạp, ảnh thật hoặc hiệu ứng 3D.
- Các chủ thể có khoảng trống đủ để chia region.
- Dừng để người dùng duyệt từng ảnh.

### Bước 3 — Tạo annotation và mở preview

- Chỉ bắt đầu sau khi ảnh được duyệt.
- Phải đọc subtitle và xem kích thước/đối tượng thật của ảnh.
- Tạo `scene-xx-name.annotation.json` cùng tên với ảnh PNG.
- `sequence` dựa trên thứ tự kể chuyện, không chỉ theo vị trí trái/phải.
- Mở preview và tải đúng thư mục cảnh.
- Dừng để người dùng duyệt region, subtitle và thứ tự.

### Bước 4 — Kiểm tra region

- Xuất ảnh kiểm tra có số thứ tự, nhãn và hướng.
- Mọi region nằm trong canvas; vùng chồng lấn có `protectedRegions` khi cần.
- Dừng để người dùng duyệt ảnh kiểm tra.

### Bước 5 — Chỉnh thời gian

- Chỉnh start/end, thứ tự, subtitle và region trên preview.
- Các vùng được vẽ tuần tự; không chồng thời gian nếu không có chủ đích rõ.
- `sceneDurationMs` phải đủ cho vùng cuối và giữ ít nhất 500 ms.
- Lưu lại đúng file annotation.
- Dừng để người dùng duyệt cấu hình cuối.

### Bước 6 — Render từng cảnh

- Chỉ render full MP4 sau khi annotation được duyệt.
- Kiểm tra ít nhất khung đầu, một khung giữa có vùng chồng lấn và khung cuối.
- Dừng để người dùng xem từng video cảnh.

### Bước 7 — Ghép video

- Chỉ ghép khi mọi cảnh đơn đã được duyệt.
- Thứ tự input phải khớp thứ tự cảnh.
- Người dùng xem video cuối và đưa yêu cầu sửa tiếp theo.

## Trạng thái UI cần có khi phát triển app

- Chưa chọn file/thư mục.
- Đang phân tích hoặc render.
- Thành công và có đường dẫn output.
- Lỗi có nguyên nhân và hành động thử lại.
- Nút bị khóa khi thao tác đang chạy hoặc input chưa hợp lệ.
- Cảnh báo trước khi ghi đè file đã tồn tại.
