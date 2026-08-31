# App desktop — Tạo video vẽ tay

MVP chạy cục bộ trên Windows, nhận một thư mục hoặc ZIP dự án rồi điều phối renderer sẵn có.

## Chạy app

Từ thư mục gốc repository:

```powershell
run_app.bat
```

Hoặc chạy thủ công:

```powershell
python scripts/prepare_env.py
.venv\Scripts\python.exe -m whiteboard_app
```

## Gói dữ liệu đầu vào

Mỗi dự án có đúng một `project.json`, ảnh và annotation cùng basename. Voice là tùy chọn.

```text
du-an/
├── project.json
├── audio/voice.mp3
└── scenes/
    ├── scene-01.png
    └── scene-01.annotation.json
```

Schema MVP:

```json
{
  "schemaVersion": 1,
  "title": "5 món thịt bò tốt cho bé",
  "version": 1,
  "voice": "audio/voice.mp3",
  "scenes": [
    {
      "id": "scene-01",
      "title": "Mở đầu",
      "image": "scenes/scene-01.png",
      "annotation": "scenes/scene-01.annotation.json"
    }
  ]
}
```

App từ chối đường dẫn tuyệt đối, đường dẫn đi ra ngoài thư mục dự án, file thiếu, scene trùng ID và ZIP không an toàn.

## Phạm vi phiên bản 0.1

- Mở thư mục, `project.json` hoặc ZIP.
- Kiểm tra cấu trúc và tài nguyên trước khi render.
- Hiển thị danh sách cảnh và nhật ký tiến trình.
- Dựng từng cảnh bằng renderer upstream rồi ghép thành `final.mp4`.
- Gắn voice bằng FFmpeg nếu dự án có `voice`.
- Có nút hủy và khóa thao tác trong lúc render.

Chưa bao gồm đồng bộ ChatGPT/MCP, tự tạo annotation, preview ảnh trực tiếp và đóng gói `.exe`.

## Kiểm tra

```powershell
python -m unittest discover -s tests -v
python -m py_compile whiteboard_app\*.py run_app.py
```
