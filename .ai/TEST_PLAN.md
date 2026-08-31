# Kế hoạch kiểm tra

## Các tầng kiểm tra

### 1. Static và syntax

```bash
python -m py_compile scripts/*.py
```

Thêm formatter/linter chỉ sau khi chốt công cụ và tránh đưa dependency lớn không cần thiết.

### 2. Unit test ưu tiên

- `parse_srt.parse_srt`: BOM, CRLF, multi-line text, dấu phẩy/dấu chấm, block thiếu index, block không có timeline.
- `parse_srt.group_scenes`: ranh giới min/target/max, cue dài, bucket cuối.
- Annotation validation: schema, canvas, region, sequence, timing, protected regions.
- Merge input validation: file thiếu, output path và fallback.

### 3. Smoke test renderer

- Dùng fixture ảnh nhỏ, annotation 2–3 vùng và duration ngắn.
- Render bằng interpreter từ `ENV_PY`.
- Mở output bằng PyAV/OpenCV để kiểm tra số frame, kích thước và duration.
- Trích frame đầu/giữa/cuối cho assertion và kiểm tra trực quan.

### 4. Kiểm tra preview browser

- Chrome/Edge trên Windows.
- Load folder có một scene hợp lệ.
- Sửa region, sequence, subtitle, start/end; lưu và mở lại.
- Kiểm tra empty folder, annotation lỗi, PNG thiếu cặp và quyền ghi bị từ chối.

### 5. Nghiệm thu người dùng

Mỗi PR có UI/render phải đưa:

- lệnh hoặc nút cần chạy;
- input mẫu;
- kết quả mong đợi;
- nơi tìm output;
- các điểm người dùng cần quan sát;
- cách gửi lại lỗi, ảnh chụp hoặc video minh chứng.

## Ma trận môi trường

| Môi trường | Mức ưu tiên | Yêu cầu |
| --- | --- | --- |
| Windows 10/11 + Chrome/Edge | Bắt buộc | Luồng người dùng chính. |
| Linux CI | Bắt buộc khi có CI | Unit/static/smoke không phụ thuộc UI. |
| macOS | Best effort | Không chặn MVP nếu chưa có người dùng mục tiêu. |

## Quy tắc bằng chứng

- Không ghi “pass” nếu lệnh chưa chạy.
- Ghi lệnh, exit code và tóm tắt output.
- Phân biệt lỗi code với lỗi môi trường/dependency.
- Không commit video lớn chỉ để chứng minh; dùng artifact hoặc link khi có hạ tầng phù hợp.
