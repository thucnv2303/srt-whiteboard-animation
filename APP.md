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
  "narration": [
    {
      "id": "dish-01",
      "sceneId": "scene-01",
      "text": "Một, cháo bò bí đỏ...",
      "elementIds": ["pumpkin-porridge"],
      "pauseBeforeMs": 200,
      "pauseAfterMs": 250
    }
  ],
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
- Danh sách bên trái hiển thị từng narration cue như một phân cảnh nội dung; dù nhiều cue dùng chung một ảnh tổng, app vẫn liệt kê và phóng đúng vùng ảnh của từng cue.
- Sau khi hoàn tất, cột trái tự chuyển sang trình phát video tích hợp: phát/tạm dừng, dừng, tua timeline, đồng hồ thời gian và âm thanh ngay trong app. Nút ↗ mở trình phát Windows chỉ là phương án dự phòng.
- Chọn tỷ lệ `16:9` (1280×720), `9:16` (1080×1920) hoặc `1:1` (1080×1080).
- Đọc và hiển thị tên, số cảnh, thời lượng và kịch bản từ gói GPT ở cột phải.
- Card **Thiết lập video** gom giọng đọc, nghe thử, cài đặt giọng, tỷ lệ đầu ra và chữ trên thân bút.
- Popup **Cài đặt giọng** quản lý đường dẫn OmniVoice và thêm giọng clone mới.
- Mẫu mới được tự chọn đoạn nói liên tục 3–8 giây, chấm điểm SNR, lọc ù/rít, giảm nhiễu nền và chuẩn hóa âm lượng.
- Nếu dự án có `narration`, OmniVoice tạo WAV riêng cho từng cue trong một lần nạp model. App lấy thời lượng WAV thực tế làm đồng hồ, tạo `timeline.json` và annotation runtime để vùng hình tương ứng vẽ cùng câu nói.
- Mỗi cue có nhịp token đệm trước khi tổng hợp; sau đó app phát hiện onset 100 ms đầu, nâng thích ứng tối đa khoảng 5 dB, nén mềm đỉnh và thêm 60 ms đệm. Cơ chế này bảo vệ từ/số đầu câu mà không tăng toàn bộ line.
- Một nút **Tạo video** chạy lần lượt: tạo voice → biên dịch timeline → dựng cảnh → ghép âm thanh và MP4 → tạo ảnh preview.
- Gắn voice bằng FFmpeg nếu dự án có `voice`.
- Có nút hủy và khóa thao tác trong lúc render.

Chưa bao gồm chạy nhiều job, đồng bộ ChatGPT/MCP, tự tạo annotation và đóng gói `.exe`.

## Dùng chung OmniVoice, không clone lại

1. Mở dự án có trường `"script": "script.txt"`; app tự đọc kịch bản, không cần copy lại.
2. Bấm **Cài đặt giọng…**, chọn `omnivoice-infer.exe` một lần.
3. Đặt tên giọng, chọn file ghi âm và bấm **Phân tích, làm sạch và lưu giọng**.
4. Nghe thử bản đã xử lý. Đóng popup, chọn giọng đó trong danh sách của màn hình chính.
5. Bấm **Tạo video**. App tự tạo toàn bộ cue voice, đồng bộ timeline rồi dựng MP4; không còn bước tạo âm thanh riêng.

Các file sinh ra nằm trong thư mục output:

```text
output/
├── audio-cues/              # WAV riêng cho từng câu
├── runtime-annotations/     # startMs/durationMs theo voice thật
├── timeline.json            # ánh xạ cue ↔ scene ↔ element
├── voice-timeline.wav       # voice hoàn chỉnh có khoảng nghỉ
├── preview.jpg              # ảnh đại diện cho khung xem video kết quả
├── preview-audio.wav        # PCM phục vụ phát/tua âm thanh trong app
└── final.mp4
```

Quy tắc mặc định: bắt đầu vẽ sau khi cue bắt đầu 100 ms, hoàn tất trước cuối câu khoảng 500 ms, nghỉ 250 ms giữa các cue và giữ hình hoàn chỉnh 500 ms cuối cảnh. App không sửa annotation nguồn do GPT gửi; chỉ dùng bản runtime khi render.

Thư viện giọng và các file WAV đã làm sạch được lưu trong `%APPDATA%\NetChuyenDong\voices`, dùng lại cho mọi dự án. Bộ lọc giúp giảm mạnh tạp âm ổn định nhưng không thể bảo đảm xóa tuyệt đối tiếng người khác, tiếng va đập lớn hoặc tiếng nhạc mà không ảnh hưởng chất giọng; luôn nghe thử trước khi lưu làm mẫu clone.

App chỉ gọi tiến trình OmniVoice bên ngoài. Đường dẫn được lưu tại
`%APPDATA%\NetChuyenDong\settings.json` để những lần mở sau không phải chọn lại. Repo này không sao chép mã nguồn, môi trường Python hoặc model của OmniVoice.

Nếu `omnivoice-infer` đã có trong `PATH`, app tự nhận lệnh đó ở lần chạy đầu.

## Kiểm tra

```powershell
python -m unittest discover -s tests -v
python -m py_compile whiteboard_app\*.py run_app.py
```

Hiện có 31 unit test cho import dự án, narration cue, danh sách phân cảnh nội dung, timeline theo WAV, bảo vệ âm đầu, annotation runtime, poster/audio preview, phép tua PCM, bảo toàn sample rate, render, UI responsive và thư viện giọng.

Trình phát tích hợp dùng PyAV để giải mã video và pygame để phát WAV. PCM nguồn luôn được bọc lại bằng WAV header trước khi đưa vào mixer 48 kHz để SDL resample đúng tốc độ trên Windows; canvas tự bỏ frame đã trễ để hình bám theo audio clock. `run_app.bat` kiểm tra dependency ở mỗi lần mở app nên máy đã có `.venv` cũng sẽ tự bổ sung pygame một lần, không cần xóa hay tạo lại môi trường.

## Gói kiểm thử 52 giây

Sau khi mở app, chọn `examples/test-52s/project.json`. Gói gồm sáu cảnh × 8,6 giây, dùng để xác nhận render nhiều cảnh và ghép `final.mp4`. Đây là fixture kỹ thuật chưa có voice.

## Dự án nội dung chân thực và voice Việt

Thư mục `examples/beef-5-dishes/` chứa dự án về năm món ăn từ thịt bò cho bé. Phiên bản 6 viết rõ “Món thứ nhất/hai/ba/tư/năm” để số thứ tự không nằm đúng biên đầu cue, đồng thời dùng bộ bảo vệ onset mới của OmniVoice. Trường `penBrand` thay chữ Trung Quốc trực tiếp trên thân cây bút bằng chữ Unicode.
