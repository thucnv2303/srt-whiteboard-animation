# Kiến trúc hiện tại

## Tổng quan

```text
ChatGPT Project / ZIP
  -> project.json schema v1
  -> whiteboard_app.project (import + validation)
  -> whiteboard_app.ui (duyệt + điều khiển)
  -> whiteboard_app.renderer (pipeline)
  -> renderer upstream từng cảnh
  -> merge_scenes.py
  -> FFmpeg gắn voice nếu có
  -> final.mp4
```

## Thành phần app

| Thành phần | Trách nhiệm |
| --- | --- |
| `whiteboard_app/project.py` | Đọc folder/JSON/ZIP, chống path traversal và trả domain model đã kiểm tra. |
| `whiteboard_app/renderer.py` | Tạo lệnh, chạy renderer từng cảnh, ghép và gắn voice. |
| `whiteboard_app/ui.py` | UI Tkinter tiếng Việt, danh sách cảnh, log, trạng thái, cancel. |
| `run_app.bat` | Chuẩn bị `.venv` lần đầu và mở app trên Windows. |
| `APP.md` | Hợp đồng dữ liệu và hướng dẫn vận hành. |

## Renderer upstream được giữ lại

| Thành phần | Trách nhiệm |
| --- | --- |
| `scripts/parse_srt.py` | Parse SRT; chưa nằm trong luồng import package MVP. |
| `assets/preview.html` | Trình chỉnh annotation cũ; sẽ được tích hợp dần. |
| `scripts/render_annotation_preview.py` | Ảnh kiểm tra region/sequence. |
| `scripts/render_stream_whiteboard.py` | Renderer chính: mask, grid/skeleton, ink/color và MP4. |
| `scripts/merge_scenes.py` | Ghép MP4 bằng FFmpeg hoặc PyAV fallback. |
| `scripts/prepare_env.py` | Tạo môi trường Python và cài dependency. |

## Hợp đồng `project.json` v1

Trường cấp dự án:

- `schemaVersion`: hiện là `1`.
- `title`: tên hiển thị.
- `version`: số nguyên dương, mặc định `1`.
- `voice`: đường dẫn tương đối tùy chọn.
- `scenes`: mảng không rỗng.

Trường scene:

- `id`: duy nhất trong dự án.
- `title`: tùy chọn.
- `image`: đường dẫn ảnh tương đối.
- `annotation`: đường dẫn annotation tương đối, cùng basename với ảnh.

## Bất biến và an toàn

- Không nhận đường dẫn tuyệt đối hoặc đường dẫn đi ra ngoài project root.
- ZIP phải có đúng một `project.json` và không chứa traversal path.
- Tài nguyên phải tồn tại trước khi bật render.
- Scene render đúng thứ tự trong manifest.
- Tác vụ dài không chạy trên UI thread.
- Không tự ghi đè `final.mp4` mà chưa hỏi người dùng.

## Khoảng trống tiếp theo

- Validator sâu cho canvas/region/timing và kích thước ảnh.
- Preview ảnh/timeline trong app.
- Tự sinh annotation từ ảnh + metadata cảnh.
- Progress phần trăm và hủy cả process tree an toàn trên Windows.
- MCP/backend cho đồng bộ media dung lượng lớn.
- Installer/`.exe` và smoke test Windows thật.

## Nguyên tắc mở rộng

- Bọc và kiểm thử script hiện có trước khi viết lại renderer.
- Domain logic tách khỏi UI để test headless.
- Thay đổi schema phải tăng version hoặc có migration.
- App không chứa khóa OpenAI và không phụ thuộc AI local.
