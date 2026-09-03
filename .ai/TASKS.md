# Hàng đợi công việc

## Task đang hoạt động

- ID: `TASK-005`
- Trạng thái: `READY_FOR_USER_TEST` sau khi cập nhật UI và pipeline một nút.
- Mục tiêu: desktop app MVP nhận gói dự án và điều phối render.
- Branch: `feat/desktop-app-mvp`
- Phạm vi: UI, schema gói dự án, pipeline, test, CI và hướng dẫn Windows.

## Hoàn thành

- `TASK-001` — Bộ kiến thức dự án; PR `#1` đã merge.
- Hợp đồng `project.json` phiên bản 1.
- Unit test cho import folder/ZIP, tài nguyên thiếu và đường dẫn không an toàn.
- App shell điều phối renderer upstream, ghép cảnh và voice tùy chọn.
- UI desktop ngang responsive, preview ảnh, dải cảnh và card log phía dưới.
- Chọn tỷ lệ video và kết nối OmniVoice dùng chung ngoài repo.
- Cột phải hiển thị metadata/kịch bản gói GPT; voice được tạo local trước khi bật render.
- Thư viện giọng dùng chung, nghe thử và popup quản lý/thêm giọng.
- Tự phân tích, chọn đoạn sạch và giảm nhiễu mẫu clone bằng FFmpeg.
- Audio-clock timeline: cue voice → thời lượng WAV → runtime annotation → render đồng bộ.
- Danh sách cue thành phân cảnh nội dung, preview video kết quả và pipeline một nút.
- Trình phát video tích hợp có hình, âm thanh, phát/tạm dừng/dừng và tua timeline.
- Tối ưu trình phát video 60 FPS: preview 30 FPS, native scaling, tái sử dụng canvas item và giảm số lần cập nhật timeline.
- Sửa player Windows: không đưa raw PCM trực tiếp vào mixer; bảo toàn sample rate bằng WAV header và chống video frame backlog.
- Bảo vệ âm đầu cue OmniVoice: token đệm, boost thích ứng và viết số thứ tự theo cụm “Món thứ…”.
- Card thiết lập video thu gọn, nơi lưu nằm trong card và vùng kịch bản lớn có thanh cuộn.
- Bộ năm job mẫu có ảnh thật, kịch bản, bốn cue timeline và ZIP để nạp đồng thời trong Multi Job.

## Backlog ưu tiên

### `TASK-002` — Baseline test SRT và môi trường

- Thêm fixture SRT và test parser BOM/timestamp/lỗi.
- Compile/smoke check toàn repo.

### `TASK-003` — Annotation đa nền tảng

- Bỏ font hard-code.
- Thêm validator annotation chi tiết và lỗi tiếng Việt.

### `TASK-007` — Nghiệm thu app MVP trên Windows

- Người dùng chạy `run_app.bat`.
- App đã mở thành công; lỗi hộp chọn dự án mở hai lần đã được sửa trên branch.
- Lỗi `UnicodeEncodeError` do renderer dùng Windows `cp1252` đã được sửa bằng môi trường UTF-8 cho subprocess.
- Đã bổ sung dự án nội dung thật về 5 món bò cho bé để nghiệm thu màu, timing và audio.
- Phiên bản 2 chuyển sang ảnh món ăn bán chân thực, voice Việt neural và nhãn bút `Ăn dặm mẹ Dâu`.
- Phiên bản 3 sửa đúng yêu cầu nghiệm thu: bỏ nhãn nổi, thay chữ Trung Quốc ngay trên thân bút.
- Mở gói demo, render và kiểm tra `final.mp4`.
- Ghi nhận ảnh lỗi, log và trải nghiệm thao tác.
- Kiểm tra resize cửa sổ ở 1280×820 và kích thước nhỏ; các card không chồng nhau.
- Kiểm tra một video 9:16 và luồng chọn voice có sẵn.
- Khi có OmniVoice sẵn, chọn CLI một lần và xác nhận lần mở app sau vẫn nhớ đường dẫn.
- Xác nhận app lấy thẳng `script.txt`, không yêu cầu copy lời thoại vào giao diện.
- Thêm một mẫu giọng thật, nghe trước/sau xử lý và đánh giá mức nhiễu còn lại hoặc méo tiếng.
- Chạy gói bò v6, xác nhận 5 câu khớp 5 vùng hình; ghi nhận offset và độ rõ âm đầu cần tinh chỉnh.
- Xác nhận cột trái hiện đủ 5 phân cảnh dù gói chỉ dùng một ảnh tổng.
- Xác nhận một lần bấm **Tạo video** tự chạy voice, timeline, render và mở được preview kết quả.
- Xác nhận player nội bộ phát tiếng, tua không lệch hình và nút ↗ mở ngoài khi cần.
- Nghe riêng đầu 5 cue, xác nhận “thứ nhất/hai/ba/tư/năm” không nhỏ hoặc hụt.
- Nạp năm ZIP tại `examples/multi-job-5-pack/zips/`, chạy toàn bộ và xác nhận job sau tự tiếp tục khi job trước hoàn tất hoặc lỗi.

### `TASK-008` — Tự tạo annotation từ scene

- Sinh region/timing cơ bản từ ảnh và metadata cảnh.
- Cho phép chỉnh trước khi render.

### `TASK-009` — Đồng bộ ChatGPT

- Chốt cơ chế MCP/backend sau khi schema v1 ổn định.
- Nhận phiên bản dự án mới mà không copy từng file.
- Báo tiến độ render trở lại ChatGPT.

### `TASK-006` — Render verification tự động

- Fixture ảnh + annotation nhỏ.
- Kiểm tra first/mid/final frame và duration.

### `TASK-010` — Multi-job bền vững

- Trạng thái: `READY_FOR_USER_TEST`; chi tiết tại `docs/MULTI_JOB_DESIGN.md`.
- M2A: đã thêm phase/progress cho pipeline và giữ nguyên luồng đơn nhiệm.
- M2B: đã có SQLite queue, một worker tuần tự, dashboard, hủy/thử lại và recovery.
- UI: dashboard ba cột responsive gồm hàng đợi thu gọn, kịch bản riêng, preview/tiến độ và log theo job.
- Thiết lập video dùng popup cho một hoặc nhiều checkbox; áp dụng đồng loạt nhưng vẫn cô lập output theo `job_id`. Job queued/running bị khóa; job hoàn tất/lỗi/đã hủy được đưa về chờ để chạy lại.
- Checkbox tiêu đề chọn/bỏ chọn toàn bộ job đang hiển thị và phản ánh trạng thái chọn một phần/toàn bộ.
- Nút Thiết lập N job nằm cạnh Chạy N job; cấu hình OmniVoice nhập tay và giọng được chọn được lưu bền vững qua lần mở app tiếp theo.
- Preview trong Đơn nhiệm và Multi Job bám theo tỷ lệ đầu ra đã chọn/lưu thay vì giữ nguyên tỷ lệ ảnh nguồn.
- M2C còn lại: worker OmniVoice sống lâu, cache cue theo nội dung và resume theo phase.
- M2D: chỉ tăng render concurrency sau benchmark; không chạy nhiều model voice đồng thời.
