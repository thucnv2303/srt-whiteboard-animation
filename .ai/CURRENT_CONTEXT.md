# Bối cảnh hiện tại

Cập nhật: 2026-09-01 UTC

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
- UI vận hành là màn hình desktop ngang, đơn nhiệm và co giãn theo kích thước cửa sổ.
- Voice hỗ trợ chọn file có sẵn hoặc gọi bản OmniVoice dùng chung bên ngoài repo.

## Phạm vi đã triển khai trong branch M1

- App shell tiếng Việt mở thư mục, `project.json` hoặc ZIP.
- Hợp đồng dữ liệu `schemaVersion: 1`.
- Chặn đường dẫn nguy hiểm, file thiếu, scene trùng và cặp tên sai.
- Danh sách cảnh, chọn output, log, khóa thao tác và hủy render.
- Điều phối render từng cảnh, ghép MP4 và gắn voice qua FFmpeg.
- Script `run_app.bat`, tài liệu `APP.md`, unit test và CI.

## Trạng thái kiểm tra

- Unit test local: 16 test pass.
- `py_compile`: pass cho app.
- UI import smoke check: pass.
- Nghiệm thu UI lần 1: app mở được trên Windows; đã sửa lỗi đóng hộp chọn file làm hộp chọn thư mục bật tiếp.
- Đã thêm gói fixture `examples/test-52s/` gồm 6 cảnh, thời lượng dự kiến 51,6 giây để người dùng kiểm tra render và merge trên Windows.
- Nghiệm thu render lần 1 phát hiện child process dùng `cp1252` và lỗi khi script in ký tự CJK; đã ép `PYTHONIOENCODING=utf-8` và `PYTHONUTF8=1` cho toàn pipeline.
- Người dùng đã dựng được MP4 có màu bằng gói `examples/beef-5-dishes/`, sau đó yêu cầu ảnh chân thực hơn và sửa voice tiếng Việt.
- Gói bò phiên bản 2 dùng ảnh món ăn bán chân thực do ImageGen tạo, voice neural `vi-VN-HoaiMyNeural` qua edge-tts; `penBrand` xóa chữ Trung Quốc và ghi Unicode trực tiếp lên thân bút.
- Chưa nghiệm thu phiên bản 2 trên Windows thật.
- UI mới có preview ảnh theo tỷ lệ, dải cảnh ngang, thiết lập bên phải và card log toàn chiều ngang ở đáy.
- Pipeline đã hỗ trợ đầu ra 16:9, 9:16 và 1:1; hai tỷ lệ mới dùng FFmpeg scale/crop giữa.
- Cấu hình OmniVoice lưu ngoài repo tại `%APPDATA%\NetChuyenDong\settings.json`; app gọi `omnivoice-infer.exe` hiện có thay vì clone/cài lại.

## Task an toàn tiếp theo

Người dùng pull branch, chạy UI ngang mới, thử đổi kích thước cửa sổ/tỷ lệ và gửi ảnh hoặc log nghiệm thu.
