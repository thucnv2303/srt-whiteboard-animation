# Bối cảnh hiện tại

Cập nhật: 2026-09-02 UTC

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
- GPT chỉ cung cấp ảnh, annotation và kịch bản; app tạo voice local bằng OmniVoice dùng chung bên ngoài repo.

## Phạm vi đã triển khai trong branch M1

- App shell tiếng Việt mở thư mục, `project.json` hoặc ZIP.
- Hợp đồng dữ liệu `schemaVersion: 1`.
- Chặn đường dẫn nguy hiểm, file thiếu, scene trùng và cặp tên sai.
- Danh sách cảnh, chọn output, log, khóa thao tác và hủy render.
- Điều phối render từng cảnh, ghép MP4 và gắn voice qua FFmpeg.
- Script `run_app.bat`, tài liệu `APP.md`, unit test và CI.

## Trạng thái kiểm tra

- Unit test local: 31 test pass.
- `py_compile`: pass cho app.
- UI import smoke check: pass.
- Nghiệm thu UI lần 1: app mở được trên Windows; đã sửa lỗi đóng hộp chọn file làm hộp chọn thư mục bật tiếp.
- Đã thêm gói fixture `examples/test-52s/` gồm 6 cảnh, thời lượng dự kiến 51,6 giây để người dùng kiểm tra render và merge trên Windows.
- Nghiệm thu render lần 1 phát hiện child process dùng `cp1252` và lỗi khi script in ký tự CJK; đã ép `PYTHONIOENCODING=utf-8` và `PYTHONUTF8=1` cho toàn pipeline.
- Người dùng đã dựng được MP4 có màu bằng gói `examples/beef-5-dishes/`, sau đó yêu cầu ảnh chân thực hơn và sửa voice tiếng Việt.
- Gói bò phiên bản 2 dùng ảnh món ăn bán chân thực do ImageGen tạo, voice neural `vi-VN-HoaiMyNeural` qua edge-tts; `penBrand` xóa chữ Trung Quốc và ghi Unicode trực tiếp lên thân bút.
- Chưa nghiệm thu phiên bản 2 trên Windows thật.
- UI mới có preview ảnh theo tỷ lệ, bảng phân cảnh nội dung, thiết lập bên phải và card log toàn chiều ngang ở đáy.
- Pipeline đã hỗ trợ đầu ra 16:9, 9:16 và 1:1; hai tỷ lệ mới dùng FFmpeg scale/crop giữa.
- Cấu hình OmniVoice lưu ngoài repo tại `%APPDATA%\NetChuyenDong\settings.json`; app gọi `omnivoice-infer.exe` hiện có thay vì clone/cài lại.
- Cột phải đọc thông tin dự án và `script.txt` từ gói GPT. Giọng, tỷ lệ và nhãn bút được gom trong card **Thiết lập video**.
- Màn hình chính chỉ chọn/nghe thử giọng đã lưu; cài đặt OmniVoice và thêm giọng mới nằm trong popup riêng.
- Voice profile dùng chung được lưu ở `%APPDATA%\NetChuyenDong\voices`; pipeline FFmpeg tự chọn đoạn 3–8 giây, ước tính SNR, high/low-pass, FFT denoise, dynamic normalize và limiter.
- Smoke test pipeline làm sạch FFmpeg: pass; cần người dùng nghiệm thu trên mẫu giọng thật.
- Schema hỗ trợ `narration[]` ánh xạ cue → scene → element. OmniVoice tạo cue trong một process để không nạp model nhiều lần.
- Timeline compiler đo thời lượng từng WAV, sinh `timeline.json`, `voice-timeline.wav` và annotation runtime; renderer ưu tiên annotation runtime mà không sửa dữ liệu nguồn.
- Gói bò phiên bản 6 có 5 cue ánh xạ trực tiếp tới 5 món; số thứ tự dùng cụm đầy đủ “Món thứ…” để tránh đặt âm số ngay biên sinh voice.
- UI coi narration cue là phân cảnh nội dung: gói bò có 1 ảnh nguồn nhưng hiển thị đủ 5 dòng, chọn từng dòng sẽ phóng đúng region món ăn.
- Chỉ còn một nút **Tạo video**; app tự chạy voice → timeline → render → ghép MP4.
- Cột trái có trình phát MP4 tích hợp bằng PyAV + pygame: phát/tạm dừng, dừng, tua, thời gian và âm thanh. FFmpeg tạo `preview-audio.wav`; nút mở ngoài chỉ là fallback.
- Nghiệm thu player phát hiện raw PCM 24 kHz có thể bị mixer Windows 48 kHz hiểu sai, làm voice nhanh/méo; đã đổi sang WAV-header resampling và bỏ toàn bộ frame canvas bị trễ để giữ A/V sync.
- Nghiệm thu voice phát hiện 100 ms đầu của cue “Hai/Ba/Bốn” thấp hơn thân câu 5–6 dB. Pipeline nay thêm token đệm, onset lift thích ứng, soft peak và 60 ms safety pad trước khi biên dịch timeline.

## Task an toàn tiếp theo

Người dùng pull branch, để `run_app.bat` tự cài pygame, rồi kiểm tra phát/tạm dừng/tua và âm thanh của video ngay trong cột trái.
