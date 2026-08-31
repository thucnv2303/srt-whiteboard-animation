# Bắt đầu làm việc với dự án

Codex trực tiếp triển khai trong repository này. Không tạo prompt để giao code cho Anti hoặc agent khác.

## Thứ tự đọc bắt buộc

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

Xác nhận ngắn gọn:

- mục tiêu người dùng;
- hành vi hiện tại và hành vi mong muốn;
- file hoặc module dự kiến sửa;
- tiêu chí kiểm tra;
- điều gì cần người dùng chạy app nghiệm thu.

## Khi hoàn thành

- Chạy kiểm tra phù hợp và ghi đúng output thực tế.
- Xem lại status, diff và file phát sinh.
- Commit trên branch task; push và mở PR khi có quyền.
- Cập nhật tài liệu trạng thái nếu cần.
- Trả cho người dùng hướng dẫn chạy/nghiệm thu ngắn gọn cùng các điểm còn mở.

## Lệnh khảo sát ban đầu

```bash
git status --short --branch
python scripts/prepare_env.py --check
python -m py_compile scripts/*.py
```

Nếu môi trường chưa có dependency, chạy `python scripts/prepare_env.py` rồi dùng interpreter được in ở dòng `ENV_PY=...`.
