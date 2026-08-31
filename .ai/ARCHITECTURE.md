# Kiến trúc hiện tại

## Tổng quan

Repo upstream là một skill/toolkit chạy local, chưa phải app tích hợp hoàn chỉnh.

```text
SRT
  -> scripts/parse_srt.py
  -> chiến lược cảnh + ảnh PNG
  -> annotation JSON + assets/preview.html
  -> scripts/render_stream_whiteboard.py
  -> MP4 từng cảnh
  -> scripts/merge_scenes.py
  -> MP4 cuối
```

## Thành phần

| Thành phần | Trách nhiệm |
| --- | --- |
| `scripts/parse_srt.py` | Đọc SRT, chuẩn hóa timestamp, tạo cue và nhóm cảnh theo thời lượng. |
| `assets/preview.html` | Giao diện local chỉnh region, sequence, subtitle, start/end và xem preview proxy. |
| `scripts/render_annotation_preview.py` | Vẽ ảnh kiểm tra region/sequence/direction lên ảnh nguồn. |
| `scripts/render_stream_whiteboard.py` | Renderer chính: mask vùng, đường bút grid/skeleton, ink/color, tay vẽ và mã hóa MP4. |
| `scripts/stream_render.py` | Logic/tiện ích render stream bổ sung của upstream; cần kiểm tra trước khi thay đổi để tránh trùng chức năng. |
| `scripts/merge_scenes.py` | Ghép MP4 bằng FFmpeg nếu có, fallback PyAV. |
| `scripts/prepare_env.py` | Tạo `.venv`, cài OpenCV, NumPy, PyAV và Pillow. |
| `assets/drawing-hand.png` | Tài nguyên tay/bút dùng khi render. |
| `SKILL.md` | Đặc tả workflow upstream bằng tiếng Trung. |

## Mô hình dữ liệu annotation

Các trường bắt buộc ở cấp cảnh:

- `sceneId`
- `canvas.width`, `canvas.height`
- `storyBasis`
- `sceneDurationMs`
- `elements[]`

Các trường chính của element:

- định danh: `id`, `label`, `type`
- kể chuyện: `sequence`, `narrativeRole`, `subtitle`
- không gian: `region {x,y,width,height}`
- hiển thị: `reveal {direction,startMs,durationMs,maskPaddingPx,protectedRegions}`
- preview: `handPath {start,end,easing}`

## Bất biến cần giữ

- Canvas khớp đúng kích thước ảnh nguồn.
- Region dùng số nguyên và nằm hoàn toàn trong canvas.
- `sequence` liên tục từ 1 và phản ánh thứ tự subtitle.
- Vùng được vẽ sau phải bị che trước thời điểm bắt đầu.
- Thời gian các vùng mặc định nối tiếp nhau.
- Khung cuối hiển thị ảnh hoàn chỉnh tối thiểu 500 ms.
- PNG và annotation phải cùng basename.

## Dependency và runtime

- Python 3 có hỗ trợ `venv`.
- Packages: `opencv-python`, `numpy`, `av`, `Pillow`.
- Chrome/Edge cho File System Access API của preview.
- FFmpeg là tùy chọn; PyAV là đường fallback cho ghép video.

## Khoảng trống cần xử lý để thành app

- Chưa có một entrypoint/UI thống nhất cho toàn bộ workflow.
- Nội dung giao diện và thông báo upstream chủ yếu là tiếng Trung.
- `render_annotation_preview.py` đang hard-code font `C:/Windows/Fonts/msyh.ttc`; cần fallback đa nền tảng và thông báo lỗi rõ.
- Chưa thấy test suite tự động hoặc fixture SRT tối thiểu trong repo.
- Chưa có CI, packaging, versioning hoặc hướng dẫn Windows bằng tiếng Việt.
- Workflow tạo ảnh nét vẽ chưa được tích hợp thành module phần mềm trong repo.

## Nguyên tắc mở rộng

- Ưu tiên bọc và kiểm thử các script hiện có trước khi viết lại renderer.
- Tách domain logic khỏi UI để có thể test không cần trình duyệt.
- Mọi thay đổi schema phải có version/migration hoặc tương thích ngược.
- Tác vụ render dài phải chạy ngoài UI thread/process chính và có progress/cancel an toàn.
