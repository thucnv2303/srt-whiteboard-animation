# Luồng sản phẩm và cổng duyệt

## Nguyên tắc

ChatGPT Project chuẩn bị nội dung sáng tạo. App desktop kiểm tra và dựng video. Người dùng vận hành app, xem kết quả và quyết định sửa hay chuyển bước; không coi sự im lặng là đồng ý.

## Luồng MVP

### Bước 1 — Chuẩn bị gói dự án

- ChatGPT hoặc người dùng tạo `project.json`, ảnh, annotation và voice tùy chọn.
- Mỗi cảnh diễn đạt một ý chính và giữ đúng thứ tự kể chuyện.
- Ảnh và annotation cùng basename.

### Bước 2 — Nhập và kiểm tra

- Người dùng mở folder, `project.json` hoặc ZIP.
- App kiểm tra schema, scene ID, đường dẫn, file và cặp tên.
- Nếu lỗi, dừng trước render và nêu rõ cách khắc phục.

### Bước 3 — Duyệt danh sách cảnh

- App hiển thị tên dự án, phiên bản, danh sách cảnh và voice.
- Người dùng xác nhận đúng gói và chọn thư mục output.
- MVP chưa tự render khi chỉ vừa mở dự án.

### Bước 4 — Render

- Chỉ bắt đầu khi người dùng bấm **Tạo video**.
- Render từng cảnh bằng annotation đã cung cấp.
- Ghép cảnh theo thứ tự trong `project.json`.
- Nếu có voice, gắn voice vào video cuối bằng FFmpeg.
- UI khóa thao tác trùng, hiển thị log và cho phép hủy.

### Bước 5 — Nghiệm thu

- App báo đường dẫn `final.mp4`.
- Người dùng xem hình, thời gian, voice và mạch nội dung.
- Yêu cầu sửa được đưa lại cho Codex hoặc ChatGPT Project tùy phần code hay nội dung.

## Luồng mục tiêu khi có đồng bộ ChatGPT

1. Người dùng nói ý tưởng trong ChatGPT Project.
2. ChatGPT tạo và gửi phiên bản dự án qua plugin/MCP.
3. App tự nhận phiên bản mới nhưng vẫn chờ người dùng bấm render.
4. App gửi trạng thái và output trở lại backend.

## Trạng thái UI bắt buộc

- Chưa chọn dự án.
- Dự án hợp lệ hoặc lỗi cụ thể.
- Đang render.
- Đã hủy.
- Thành công và có đường dẫn output.
- Lỗi có nguyên nhân và hành động thử lại.
- Nút bị khóa khi thao tác đang chạy hoặc input chưa hợp lệ.
- Cảnh báo trước khi ghi đè `final.mp4`.

