# App desktop — Studio video vẽ tay

App đơn nhiệm chạy cục bộ trên Windows, nhận `project.json` hoặc ZIP rồi điều phối renderer sẵn có.

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

Mỗi dự án GPT có đúng một `project.json`, `script.txt`, ảnh và annotation cùng basename. GPT không cần tạo voice; app dùng OmniVoice trên máy để tạo file âm thanh sau khi quét dự án.

```text
du-an/
├── project.json
├── script.txt
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
  "script": "script.txt",
  "penBrand": "Ăn dặm mẹ Dâu",
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

- Giao diện desktop ngang; khung xem trước, thiết lập và danh sách cảnh co giãn theo cửa sổ.
- Khi cửa sổ hẹp, khối thiết lập tự chuyển xuống dưới khung xem trước.
- Card nhật ký toàn chiều ngang luôn nằm ở dưới cùng.
- Mở `project.json` hoặc ZIP.
- Kiểm tra cấu trúc và tài nguyên trước khi render.
- Xem trước ảnh và chuyển cảnh bằng dải cảnh ngang.
- Chọn tỷ lệ `16:9` (1280×720), `9:16` (1080×1920) hoặc `1:1` (1080×1080).
- Đọc và hiển thị tên, số cảnh, thời lượng và kịch bản từ gói GPT ở cột phải.
- Tạo voice từ kịch bản bằng bản OmniVoice đã cài ở nơi khác trên máy.
- Dựng từng cảnh bằng renderer upstream rồi ghép thành `final.mp4`.
- Gắn voice bằng FFmpeg nếu dự án có `voice`.
- Có nút hủy và khóa thao tác trong lúc render.

Chưa bao gồm chạy nhiều job, đồng bộ ChatGPT/MCP, tự tạo annotation và đóng gói `.exe`.

## Dùng chung OmniVoice, không clone lại

1. Mở dự án có trường `"script": "script.txt"`; app tự đọc kịch bản, không cần copy lại.
2. Trong mục **Tạo âm thanh bằng OmniVoice**, bấm **Chọn OmniVoice…** và chọn `omnivoice-infer.exe` trong môi trường đang có trên máy.
3. Chọn một file giọng mẫu rồi bấm **Tạo âm thanh từ kịch bản**.
4. Khi voice hoàn tất, nút **Tạo video** mới được bật.

App chỉ gọi tiến trình OmniVoice bên ngoài. Đường dẫn được lưu tại
`%APPDATA%\NetChuyenDong\settings.json` để những lần mở sau không phải chọn lại. Repo này không sao chép mã nguồn, môi trường Python hoặc model của OmniVoice.

Nếu `omnivoice-infer` đã có trong `PATH`, app tự nhận lệnh đó ở lần chạy đầu.

## Kiểm tra

```powershell
python -m unittest discover -s tests -v
python -m py_compile whiteboard_app\*.py run_app.py
```

Hiện có 18 unit test cho import dự án, kịch bản GPT, an toàn ZIP, lệnh render, tỷ lệ video, UI responsive và cấu hình OmniVoice.

## Gói kiểm thử 52 giây

Sau khi mở app, chọn `examples/test-52s/project.json`. Gói gồm sáu cảnh × 8,6 giây, dùng để xác nhận render nhiều cảnh và ghép `final.mp4`. Đây là fixture kỹ thuật chưa có voice.

## Dự án nội dung chân thực và voice Việt

Thư mục `examples/beef-5-dishes/` chứa dự án khoảng 50 giây về năm món ăn từ thịt bò cho bé. Trên Windows, chạy `create-voice-neural.bat` một lần để tạo `voice.mp3`, rồi mở `project.json` bằng app. Voice neural cần Internet lúc tạo nhưng không cần API key. Trường `penBrand` thay chữ Trung Quốc trực tiếp trên thân cây bút bằng chữ Unicode.
