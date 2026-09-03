# App desktop — Studio video vẽ tay

App chạy cục bộ trên Windows, hỗ trợ cả chế độ đơn nhiệm và hàng đợi multi-job nhận `project.json` hoặc ZIP rồi điều phối renderer sẵn có.

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
- Khung preview đổi ngay theo tỷ lệ đã chọn; trong Multi Job, preview đọc tỷ lệ đã lưu riêng của job sau khi bấm lưu thiết lập.
- Popup **Thiết lập job** có preview riêng: bấm `16:9`, `9:16` hoặc `1:1` sẽ thấy vùng crop đổi ngay trước khi lưu.
- Đọc và hiển thị tên, số cảnh, thời lượng và kịch bản từ gói GPT ở cột phải.
- Card **Thiết lập video** mặc định thu gọn; bấm tiêu đề để mở giọng đọc, nghe thử, cài đặt giọng, tỷ lệ đầu ra, chữ trên thân bút và nơi lưu kết quả.
- Vùng kịch bản chiếm phần không gian còn lại của cột phải, dùng cỡ chữ lớn hơn và có thanh cuộn cho nội dung dài.
- Nút **MULTI JOB** mở dashboard ba cột: hàng đợi thu gọn, kịch bản ở giữa và preview/tiến độ ở bên phải; log riêng nằm phía dưới.
- Nút **Chạy N job** xếp các job đang chờ hoặc đưa job lỗi/đã hủy được đánh dấu về chờ để chạy lại; **Bắt đầu hàng đợi** xếp toàn bộ job đang chờ.
- Popup **Thiết lập video…** áp dụng cho toàn bộ checkbox đang chọn. Khi sửa nhiều job, nơi lưu là thư mục gốc và app tự tạo thư mục con riêng theo `job_id`.
- Nút **Thiết lập N job** nằm ngay cạnh **Chạy N job** trong thanh công cụ hàng đợi.
- Hàng đợi được lưu bằng SQLite; đóng/mở app không mất danh sách. Job đang chạy khi app đóng được đánh dấu lỗi gián đoạn để người dùng chạy lại.
- Popup **Cài đặt giọng** quản lý đường dẫn OmniVoice và thêm giọng clone mới.
- Mẫu mới được tự chọn đoạn nói liên tục 3–8 giây, chấm điểm SNR, lọc ù/rít, giảm nhiễu nền và chuẩn hóa âm lượng.
- Nếu dự án có `narration`, OmniVoice tạo WAV riêng cho từng cue trong một lần nạp model. App lấy thời lượng WAV thực tế làm đồng hồ, tạo `timeline.json` và annotation runtime để vùng hình tương ứng vẽ cùng câu nói.
- Mỗi cue có nhịp token đệm trước khi tổng hợp; sau đó app phát hiện onset 100 ms đầu, nâng thích ứng tối đa khoảng 5 dB, nén mềm đỉnh và thêm 60 ms đệm. Cơ chế này bảo vệ từ/số đầu câu mà không tăng toàn bộ line.
- Một nút **Tạo video** chạy lần lượt: tạo voice → biên dịch timeline → dựng cảnh → ghép âm thanh và MP4 → tạo ảnh preview.
- Gắn voice bằng FFmpeg nếu dự án có `voice`.
- Có nút hủy và khóa thao tác trong lúc render.

Chưa bao gồm render song song, cache cue OmniVoice, đồng bộ ChatGPT/MCP, tự tạo annotation và đóng gói `.exe`. Kiến trúc hàng đợi và lộ trình nâng concurrency nằm trong `docs/MULTI_JOB_DESIGN.md`.

## Dùng chế độ Multi job

1. Cấu hình OmniVoice và chọn giọng trong màn hình **Đơn nhiệm**. Đây là cấu hình mặc định khi thêm job mới.
2. Chuyển sang **MULTI JOB**, bấm **Thêm dự án** và chọn một hoặc nhiều `project.json`/ZIP.
3. Mỗi job chụp riêng giọng, tỷ lệ khung hình và chữ trên bút tại thời điểm được thêm. Thay đổi thiết lập về sau không làm đổi job cũ.
4. Đánh dấu checkbox rồi bấm **Chạy N job**, hoặc bấm **Bắt đầu hàng đợi** để chạy tất cả job đang chờ.
5. Bấm KPI **Tổng job / Đang chạy / Đang chờ / Hoàn tất / Lỗi** để lọc bảng. Việc lọc không xóa lựa chọn checkbox.
6. Chọn một dòng để xem kịch bản, cấu hình snapshot, preview, log và thư mục output của job đó.

Job **Đang chờ**, **Lỗi**, **Đã hủy** hoặc **Hoàn tất** có thể sửa trực tiếp trong popup **Thiết lập video…**, không cần xóa và thêm lại. Nếu đang tích nhiều checkbox, giọng đọc, tỷ lệ, chữ trên bút và thư mục gốc được áp dụng đồng loạt; mỗi job vẫn dùng một thư mục con riêng. Khi lưu job lỗi/đã hủy/hoàn tất, app tự đưa job về trạng thái chờ và giữ đánh dấu để chạy lại. Chỉ job đã xếp chạy hoặc đang chạy bị khóa để worker không đọc một snapshot đang thay đổi.

Tỷ lệ và chữ trên bút được nhớ trong `%APPDATA%\NetChuyenDong\settings.json`, cùng tệp cấu hình OmniVoice nhưng mỗi nhóm thiết lập được cập nhật độc lập. Mở lại app hoặc thêm job mới sẽ dùng lựa chọn gần nhất. Job còn ở trạng thái đã xếp từ phiên trước được trả về **Đang chờ**; worker chỉ bắt đầu sau khi người dùng bấm nút Chạy/Bắt đầu trong phiên hiện tại.

Checkbox ở tiêu đề bảng chọn/bỏ chọn toàn bộ job đang hiển thị, trừ job đang chạy. Biểu tượng `☐ / ▣ / ☑` lần lượt thể hiện chưa chọn, chọn một phần và chọn tất cả. Nút **Chạy N job** đếm job đang chờ cùng job lỗi/đã hủy có thể đưa về chờ để chạy lại.

Worker xử lý tuần tự một job tại một thời điểm. **Tạm dừng hàng đợi** chỉ ngăn lấy job tiếp theo; công đoạn đang chạy vẫn hoàn tất an toàn. **Hủy job** dừng job đang chọn. Đánh dấu job lỗi rồi bấm **Chạy N job** để chạy lại; các job sau vẫn tiếp tục.

### Bộ kiểm tra 5 job

Repository có sẵn năm dự án nội dung thật tại `examples/multi-job-5-pack/`. Để nạp cả bộ trong một thao tác:

1. Bấm **+ Thêm dự án** trong màn hình Multi Job.
2. Mở `examples/multi-job-5-pack/zips/`.
3. Chọn đồng thời cả năm file ZIP rồi bấm **Open**.
4. Giữ cả năm checkbox được chọn và bấm **Chạy 5 job**.

Các chủ đề gồm trái cây mùa hè, thói quen tập trung, chăm cây trong căn hộ, đồ uống ngày mưa và điểm đến thiên nhiên. Mỗi job có một ảnh nguồn 16:9, bốn narration cue và bốn vùng reveal tương ứng. Voice được tạo mới bằng OmniVoice trên máy, giống luồng dự án thật.

Database nằm tại `%APPDATA%\NetChuyenDong\jobs.db`. Mỗi lần chạy được cô lập:

```text
<thu-muc-du-an>/output/runs/<job_id>/
├── audio-cues/
├── runtime-annotations/
├── timeline.json
├── voice-timeline.wav
├── preview.jpg
├── preview-audio.wav
└── final.mp4
```

Gói ZIP dùng `%APPDATA%\NetChuyenDong\runs\<job_id>\` vì thư mục giải nén chỉ tồn tại tạm thời.

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
Đường dẫn được lưu cả khi gõ/dán trực tiếp, bấm **Lưu**, chọn file, bắt đầu xử lý giọng hoặc đóng popup. Giọng vừa tạo/chọn cũng được ghi nhớ cho lần mở tiếp theo.

Nếu `omnivoice-infer` đã có trong `PATH`, app tự nhận lệnh đó ở lần chạy đầu.

## Kiểm tra

```powershell
python -m unittest discover -s tests -v
python -m py_compile whiteboard_app\*.py run_app.py
```

Hiện có 60 unit test cho import dự án, narration cue, danh sách phân cảnh nội dung, timeline theo WAV, bảo vệ âm đầu, annotation runtime, poster/audio preview, tỷ lệ khung preview, phép tua PCM, bảo toàn sample rate, render, UI responsive, SQLite job store, worker tuần tự, chống tự chạy job cũ, hủy job, job lỗi tiếp tục hàng đợi, KPI/filter, chọn tất cả, thiết lập hàng loạt và lưu cấu hình giọng/video.

Trình phát tích hợp dùng PyAV để giải mã video và pygame để phát WAV. PCM nguồn luôn được bọc lại bằng WAV header trước khi đưa vào mixer 48 kHz để SDL resample đúng tốc độ trên Windows; canvas tự bỏ frame đã trễ để hình bám theo audio clock. Preview được giới hạn tối đa 30 FPS, resize bằng libswscale và chỉ cập nhật thanh thời gian 5 lần/giây để video 60 FPS không làm nghẽn UI; file MP4 đầu ra không bị hạ FPS. `run_app.bat` kiểm tra dependency ở mỗi lần mở app nên máy đã có `.venv` cũng sẽ tự bổ sung pygame một lần, không cần xóa hay tạo lại môi trường.

## Gói kiểm thử 52 giây

Sau khi mở app, chọn `examples/test-52s/project.json`. Gói gồm sáu cảnh × 8,6 giây, dùng để xác nhận render nhiều cảnh và ghép `final.mp4`. Đây là fixture kỹ thuật chưa có voice.

## Dự án nội dung chân thực và voice Việt

Thư mục `examples/beef-5-dishes/` chứa dự án về năm món ăn từ thịt bò cho bé. Phiên bản 6 viết rõ “Món thứ nhất/hai/ba/tư/năm” để số thứ tự không nằm đúng biên đầu cue, đồng thời dùng bộ bảo vệ onset mới của OmniVoice. Trường `penBrand` thay chữ Trung Quốc trực tiếp trên thân cây bút bằng chữ Unicode.
