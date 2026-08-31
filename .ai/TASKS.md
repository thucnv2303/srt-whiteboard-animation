# Hàng đợi công việc

## Task đang hoạt động

- ID: `TASK-001`
- Trạng thái: `WAITING_USER_REVIEW`
- Mục tiêu: đưa bộ kiến thức dự án lên repo GitHub riêng của người dùng.
- Branch: `docs/bootstrap-project-knowledge`
- PR: https://github.com/thucnv2303/srt-whiteboard-animation/pull/1
- Tiến độ: branch đã push và PR đã mở; chờ người dùng duyệt.

## Backlog ưu tiên

### `TASK-002` — Baseline test và kiểm tra môi trường

- Thêm fixture SRT tối thiểu.
- Test parser với BOM, dấu phẩy/dấu chấm milliseconds, block lỗi và SRT rỗng.
- Chạy compile/smoke check trên Windows-oriented workflow.

### `TASK-003` — Sửa preview annotation đa nền tảng

- Bỏ hard-code duy nhất `C:/Windows/Fonts/msyh.ttc`.
- Có danh sách font fallback và thông báo lỗi tiếng Việt.
- Validate tham số CLI và cấu trúc annotation.

### `TASK-004` — Việt hóa trải nghiệm hiện tại

- Rà soát `assets/preview.html` và output CLI.
- Việt hóa label, trạng thái, validation và lỗi mà không phá schema.

### `TASK-005` — Chọn và dựng app shell MVP

- Chốt với người dùng: desktop local hay web local.
- Tạo entrypoint thống nhất cho chọn SRT, quản lý scene, mở preview và theo dõi render.
- Không viết lại renderer khi chưa có lý do kỹ thuật được chứng minh.

### `TASK-006` — Render verification tự động

- Fixture ảnh + annotation nhỏ.
- Kiểm tra first/mid/final frame, thời lượng và vùng chưa được vẽ.
- Tránh commit video nặng; dùng artifact CI hoặc fixture tối giản.

## Hoàn thành

- Khảo sát repo upstream và chuyển đổi mô hình vận hành — tài liệu local ngày 2026-08-31.
- Tạo fork làm việc, push branch và mở PR bootstrap `#1` — ngày 2026-08-31.
