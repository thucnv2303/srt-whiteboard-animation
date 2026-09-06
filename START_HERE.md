# Bắt đầu làm việc với dự án

Codex trực tiếp triển khai trong repository này. Không tạo prompt để giao code cho Anti hoặc agent khác.

## Chạy app trên Windows

1. Clone hoặc tải repository về máy.
2. Nhấp đúp `run_app.bat`.
3. Lần chạy đầu app tự chuẩn bị môi trường Python.
4. Chọn thư mục, `project.json` hoặc ZIP dự án.
5. Chọn nơi xuất và bấm **Tạo video**.

Định dạng gói đầu vào và cách xử lý lỗi nằm trong `APP.md`.

## Thứ tự đọc bắt buộc khi phát triển

1. `AGENTS.md`
2. `.ai/PROJECT_BRIEF.md`
3. `.ai/PRODUCT_WORKFLOW.md`
4. `.ai/ARCHITECTURE.md`
5. `.ai/CURRENT_CONTEXT.md`
6. `.ai/DECISIONS.md`
7. `.ai/TASKS.md`
8. `.ai/ACCEPTANCE_CRITERIA.md`
9. `.ai/TEST_PLAN.md`
10. Source, test và config liên quan trực tiếp tới task

## Trước khi sửa code

Xác nhận ngắn gọn mục tiêu, hành vi mong muốn, module dự kiến sửa, tiêu chí kiểm tra và phần người dùng cần chạy nghiệm thu.

## Khi hoàn thành

- Chạy kiểm tra phù hợp và ghi đúng output thực tế.
- Xem lại status, diff và file phát sinh.
- Commit trên branch task; push và mở PR khi có quyền.
- Cập nhật tài liệu trạng thái nếu cần.
- Trả hướng dẫn chạy/nghiệm thu ngắn gọn cùng các điểm còn mở.

## Lệnh khảo sát ban đầu

```bash
git status --short --branch
python scripts/prepare_env.py --check
python -m py_compile scripts/*.py whiteboard_app/*.py
python -m unittest discover -s tests -v
```

