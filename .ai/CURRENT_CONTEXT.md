# Bối cảnh hiện tại

Cập nhật: 2026-08-31 UTC

## Milestone hiện tại

M1 — Dựng desktop app MVP nhận gói dự án và điều phối renderer local.

## Trạng thái repository

- Repo làm việc: `thucnv2303/srt-whiteboard-animation`
- Base branch: `main`
- Base SHA: `5eda67e6e52cc2575de4fc15277d0fc3c6d04d7c`
- Working branch: `feat/desktop-app-mvp`
- PR bootstrap `#1`: đã merge.
- CI: workflow compile + unit test được bổ sung trong branch M1.

## Quyết định sản phẩm mới

- ChatGPT Project sẽ đảm nhiệm ý tưởng, kịch bản, voice và có thể cả ảnh.
- App local không gọi AI; app nhận gói dữ liệu chuẩn, kiểm tra và dựng video.
- App đầu tiên là desktop Windows dùng Python/Tkinter để tận dụng renderer hiện tại.
- Đồng bộ ChatGPT/MCP làm sau khi hợp đồng `project.json` và pipeline local ổn định.

## Phạm vi đã triển khai trong branch M1

- App shell tiếng Việt mở thư mục, `project.json` hoặc ZIP.
- Hợp đồng dữ liệu `schemaVersion: 1`.
- Chặn đường dẫn nguy hiểm, file thiếu, scene trùng và cặp tên sai.
- Danh sách cảnh, chọn output, log, khóa thao tác và hủy render.
- Điều phối render từng cảnh, ghép MP4 và gắn voice qua FFmpeg.
- Script `run_app.bat`, tài liệu `APP.md`, unit test và CI.

## Trạng thái kiểm tra

- Unit test local: 8 test pass.
- `py_compile`: pass cho app.
- UI import smoke check: pass.
- Nghiệm thu UI lần 1: app mở được trên Windows; đã sửa lỗi đóng hộp chọn file làm hộp chọn thư mục bật tiếp.
- Chưa chạy render MP4 đầy đủ trong môi trường Windows thật.
- Chưa có nghiệm thu người dùng.

## Task an toàn tiếp theo

Người dùng chạy app demo trên Windows và gửi ảnh/lỗi. Sau đó sửa theo nghiệm thu trước khi thêm tự tạo annotation hoặc đồng bộ ChatGPT.
