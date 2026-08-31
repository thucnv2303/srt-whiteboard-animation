# Hàng đợi công việc

## Task đang hoạt động

- ID: `TASK-005`
- Trạng thái: `READY_FOR_USER_TEST` sau khi PR được tạo.
- Mục tiêu: desktop app MVP nhận gói dự án và điều phối render.
- Branch: `feat/desktop-app-mvp`
- Phạm vi: UI, schema gói dự án, pipeline, test, CI và hướng dẫn Windows.

## Hoàn thành

- `TASK-001` — Bộ kiến thức dự án; PR `#1` đã merge.
- Hợp đồng `project.json` phiên bản 1.
- Unit test cho import folder/ZIP, tài nguyên thiếu và đường dẫn không an toàn.
- App shell điều phối renderer upstream, ghép cảnh và voice tùy chọn.

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
- Mở gói demo, render và kiểm tra `final.mp4`.
- Ghi nhận ảnh lỗi, log và trải nghiệm thao tác.

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
