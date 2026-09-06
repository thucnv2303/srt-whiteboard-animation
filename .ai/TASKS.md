# Hàng đợi công việc

## Task đang hoạt động

- ID: `TASK-005`
- Trạng thái: `READY_FOR_USER_TEST` sau khi cập nhật UI và pipeline một nút.
- Mục tiêu: desktop app MVP nhận gói dự án và điều phối render.
- Branch: `feat/desktop-app-mvp`
- Phạm vi: UI, schema gói dự án, pipeline, test, CI và hướng dẫn Windows.

## Hoàn thành

- `TASK-037` — Thuật toán Tối ưu Không Gian Tự Động (Auto Space Maximizer & Large Typography) cho Toàn bộ 330 Slot: Khắc phục lỗi chữ Cảnh 1 bị bé lọt thỏm (giữ tiêu đề 1 dòng to $34px$, bullet $26px$) và Cảnh 3 thừa nhiều khoảng trống bên dưới (nâng khung lên $185px$, chữ mô tả $26px$, line-height $38px$). Đã xuất trọn bộ 4 cảnh tĩnh cho Slot 3 và đạt chuẩn TECHNICALLY_VERIFIED (70/70 pytest pass).

- `TASK-001` — Bộ kiến thức dự án; PR `#1` đã merge.
- Hợp đồng `project.json` phiên bản 1.
- Unit test cho import folder/ZIP, tài nguyên thiếu và đường dẫn không an toàn.
- App shell điều phối renderer upstream, ghép cảnh và voice tùy chọn.
- UI desktop ngang responsive, preview ảnh, dải cảnh và card log phía dưới.
- Chọn tỷ lệ video và kết nối OmniVoice dùng chung ngoài repo.
- Cột phải hiển thị metadata/kịch bản gói GPT; voice được tạo local trước khi bật render.
- Thư viện giọng dùng chung, nghe thử và popup quản lý/thêm giọng.
- Tự phân tích, chọn đoạn sạch và giảm nhiễu mẫu clone bằng FFmpeg.
- Audio-clock timeline: cue voice → thời lượng WAV → runtime annotation → render đồng bộ.
- Danh sách cue thành phân cảnh nội dung, preview video kết quả và pipeline một nút.
- Trình phát video tích hợp có hình, âm thanh, phát/tạm dừng/dừng và tua timeline.
- Tối ưu trình phát video 60 FPS: preview 30 FPS, native scaling, tái sử dụng canvas item và giảm số lần cập nhật timeline.
- Sửa player Windows: không đưa raw PCM trực tiếp vào mixer; bảo toàn sample rate bằng WAV header và chống video frame backlog.
- Bảo vệ âm đầu cue OmniVoice: token đệm, boost thích ứng và viết số thứ tự theo cụm “Món thứ…”.
- Bộ năm job mẫu có ảnh thật, kịch bản, bốn cue timeline và ZIP để nạp đồng thời trong Multi Job.
- `TASK-011` — Hệ thống Agent và kho tri thức khoa học cho kênh "Ăn dặm mẹ Dâu" (Agent prompt, Knowledge Base WHO/Viện Dinh Dưỡng, References truy xuất, ma trận 30 ngày x 3 bài/ngày và template 9:16).
- `TASK-012` — Tăng tốc GPU & Tối ưu Render Pipeline: tích hợp phát hiện GPU Encoder (`h264_mf` / `h264_nvenc`), giảm FPS 60->30, canvas uint8 và gom nhóm nét vẽ cục bộ `_reveal_ink_segments`, tăng tốc độ render thực tế lên gấp 40 lần.
- `TASK-013` — Kịch bản liền mạch (Seamless Storytelling) & Đồng bộ tốc độ video theo Voice: viết kịch bản liền mạch có câu chuyển ý, render voice cả đoạn trước bằng OmniVoice, đo thời lượng và tự động co giãn tốc độ vẽ khớp 100% với giọng đọc, đóng gói `day_01_seamless`.
- `TASK-014` — Bổ sung trường văn bản đối chiếu (referenceText) trong Voice Manager Dialog & Thuật toán Adaptive Onset Energy Compensation loại bỏ triệt để hiện tượng hụt hơi âm đầu.
- `TASK-015` — Bổ sung tính năng Xóa giọng đọc (Delete Voice Clone) trong Thư viện giọng: thêm nút "Xóa giọng", hộp thoại xác nhận an toàn, dọn dẹp file WAV mẫu và cập nhật cấu hình bền vững.
- `TASK-016` — Scene-Level Seamless Voice Pipeline & Tự động đồng bộ nét vẽ theo Voice (Keyword Alignment): Tạo voice liền mạch 1 luồng theo từng cảnh trong 1 lần nạp model duy nhất, loại bỏ hoàn toàn âm đệm "hờ/ồ"; tự động phân tích mốc thời gian từ khóa bằng Whisper để khớp nét vẽ của từng phần tử với giọng đọc, co giãn tốc độ vẽ mượt mà và giữ 700ms gaze time cuối cảnh; tích hợp vào single-job và multi-job runner; 70 unit tests PASS.
- `TASK-017` — Khắc phục độ trễ chuyển cảnh, nâng cấp Typography thẻ chữ và tích hợp âm thanh SFX chuyển cảnh: Giảm `gaze_ms` về 250ms, bổ sung hiệu ứng `xfade wipeleft 0.25s` bằng GPU MFT trong `scripts/merge_scenes.py`, thiết kế lại thẻ chữ 44-52px rõ nét không bị lỗi ô vuông unicode, tích hợp Whoosh SFX vào timeline; 70 unit tests PASS.
- `TASK-018` — Nâng cấp độ phân giải 2K / 4K, khắc phục triệt để video bị mờ, đồng bộ màu canvas và thương hiệu thân bút: Bổ sung các preset độ phân giải 16:9, 9:16 (1080p, 2K 1440x2560, 4K 2160x3840), 1:1; trích xuất màu nền thực tế gán cho canvas để loại bỏ hoàn toàn viền lem/giật màu nhấp nháy; co giãn kích thước tay vẽ theo chiều cao khung hình; tự động in thương hiệu "Ăn dặm mẹ Dâu" lên thân bút; tăng bitrate encoder lên 15M / crf 18; render hoàn tất video 2K `projects/day_01_an_dam_v2/output/final.mp4`; 70 unit tests PASS.
- `TASK-019` — Tái tạo bộ 4 ảnh hoạt hình sinh động, sửa triệt để Bounding Box 100% độ phủ và thuật toán tự động cắt lọc âm hallucination ("đỏ", "dễ ăn"): Tạo mới bộ 4 ảnh Visual Storytelling hoạt hình thiếu nhi ấm áp giàu cảm xúc nhân vật; thiết kế thẻ chữ bo góc rõ nét; tối ưu vùng vẽ liên tục $x \in [0, 1080]$ đạt độ phủ 100% (xóa bỏ lỗi cắt cụt nửa dưới Cảnh 3); cắt tỉa file mẫu Xuân Dung và tích hợp `trim_leading_hallucination` tự động loại bỏ triệt để âm rác đầu câu; render hoàn tất video 2K `projects/day_01_an_dam_v2/output/final.mp4` (43.9s, 68.0 MB); 70 unit tests PASS.
- `TASK-020` — Tích hợp Google Sheets Webhook Gateway 2 chiều: Xây dựng Apps Script Webhook API tự động ghi đè và đồng bộ 330 kịch bản video (30 ngày x 11 video/ngày) vào Google Sheet; cấu trúc 14 cột chuyên biệt (tách riêng YouTube Title & Description, thêm chuyên mục thứ 11 "Tâm tư ăn dặm & Thổ lộ cảm xúc mẹ bỉm"); lưu cấu hình tại `config/google_sheets_config.json`.
- `TASK-021` — Xuất bản tự động video Ngày 1 vào Google Drive và cập nhật Sheets: Đã xuất file video hoàn chỉnh 2K (1440x2560 30FPS, 71.3 MB) vào thư mục `G:\My Drive\Đăng video\Day_01_Slot_01_3_Ngay_Vang_Khoi_Dong_Cho_Be_6_Thang_2K.mp4` và gọi Webhook cập nhật trạng thái `READY_TO_PUBLISH (2K 1440x2560)` lên Google Sheets thành công.
- `TASK-023` — Cập nhật Typography thẻ chữ to rõ ràng, loại bỏ âm thanh Whoosh, nâng cấp hiệu ứng chuyển trang (slideleft) và nguyên tắc vẽ từ trên xuống dưới (top-to-bottom).
- `TASK-024` — Sửa triệt để lỗi chữ đứt nét, kịch bản voice y khoa cặn kẽ chi tiết và điều chỉnh nhịp xem thư thái (84.6s, gaze 1000ms):
  + Tách độc lập minh họa và thẻ chữ trong `annotation.json`; tối ưu dải mật độ text và chống nhảy lùi nét trong `scripts/stream_render.py`.
  + Nâng cấp kịch bản chuyên gia cặn kẽ từng gram, ml, thời gian ninh nhỏ lửa 45 phút, rây 0.5mm, 1-2 thìa cà phê đầu đời và theo dõi dị ứng 3 ngày.
  + Tăng thời lượng lên 84.6s và kéo dài thời gian dừng tĩnh cuối mỗi cảnh `gaze_ms = 1000` (1.0s), loại bỏ cảm giác xem bị "đuổi".
  + Xuất bản video 2K 1440x2560 sang Google Drive `G:\My Drive\Đăng video` và cập nhật Google Sheets thành công.
- `TASK-025` — Nâng cấp hệ thống hình khối đồ họa vẽ tay đa dạng nghệ thuật (Xóa bỏ định dạng khung chữ nhật đơn diệu):
  + Thay thế khung chữ nhật đồng loạt bằng 5 dạng hình khối nghệ thuật vẽ tay cao cấp phong cách sách tranh thiếu nhi: Dải ruy băng cuộn 3D gấp mép (3D Swallowtail Ribbon Banner), Bong bóng thoại comic (Comic Speech Bubble) có đuôi chỉ nhân vật, Thẻ ghi chú dán băng keo Washi (Washi Memo Card), Huy hiệu số tròn dập nổi (Circular Badges ❶ ❷ ❸) kèm tag viên thuốc (Pill Badges), Thẻ CTA bo tròn nhấn trái tim vector toán học (Vector Hearts).
  + Nét vẽ tay lượn theo đường cong ruy băng và bong bóng sống động tự nhiên, không bị giật hay nhảy nét.
  + Render hoàn tất video 2K (1440x2560 30FPS, 122.53 MB, 84.8s) xuất thẳng sang `G:\My Drive\Đăng video\Day_01_Slot_02_Gạo_Tẻ_Nấu_Cháo_Rây_Bé_Mấy_Tháng_Ăn_Được_2K.mp4` và gửi webhook đồng bộ Google Sheets thành công.
- `TASK-032` — Khắc phục triệt để lỗi chữ tràn khung & Nâng cấp Hệ thống Hình khối Nghệ thuật Vẽ tay Sinh động.
- `TASK-034` — Khắc phục triệt để lỗi ảnh Cảnh 3 bị che mất góc & Cơ chế tự động tính chiều cao khung card ăn khớp theo câu chữ: Tái cấu trúc phân vùng Scene 3 theo dải cao toàn màn hình $[0, 1080]$, xóa bỏ triệt để hiện tượng cắt góc ảnh; nâng cấp `draw_step_pill_badge` tự động tính chiều cao theo số dòng text và truyền trực tiếp bounding box thực tế vào `annotation.json`; re-render và kiểm chứng thành công trên Day 1 Slot 03 (53.9s 2K).
- ID: `TASK-036` — Cơ chế Tự động Ép Biên An Toàn (Safe Margin Inward Clamping) & Auto-fit Card Cảnh 3 cho Toàn bộ 330 Slot:
  + Phát hiện nguyên nhân cốt lõi khiến mép phải khung card Cảnh 3 bị xén mất góc ở các slot: `draw_step_pill_badge` nhận tọa độ `x=750` kết hợp `card_width=620` làm mép phải vọt lên $1438px$, vượt quá độ phân giải màn hình $1080px$.
  + Triển khai thuật toán Inward Clamping trong `whiteboard_app/art_shapes.py`: nếu $x_1 > 1040px$, tự động lùi $x$ sang trái theo $\Delta x$ để giữ $x_1 \le 1040px$, đồng thời vẽ huy hiệu số tròn sau khi $x$ đã căn chỉnh để toàn bộ cụm thẻ + huy hiệu luôn đồng bộ và nằm trọn vẹn 100% trong khung hình.
  + Đã xuất ảnh kiểm thử tĩnh cho Cảnh 3 Slot 03 mà không cần render video theo đúng chỉ thị.
- `TASK-035` — Khắc phục triệt để lỗi chữ dính dòng / thẻ pill méo Cảnh 1 & Xóa bỏ hardcode phụ đề Cảnh 4 bằng Universal Advice Cards:
  + Tách dòng bullet theo `\n` trong `draw_auto_card_text`: xóa bỏ lỗi dính 2 gạch đầu dòng trên 1 hàng.
  + Thẻ cảnh báo dạng viên nang tự co giãn `draw_warning_pill`: ôm sát chiều rộng text + icon, xóa bỏ hiện tượng thẻ dài ngoằng và chữ bị dồn ép.
  + Thẻ lời khuyên vạn năng `draw_advice_card`: thay thế các huy hiệu cố định thìa/mặt trời/lịch bằng thẻ số tròn ❶ ❷ ❸ đa sắc màu mang bóng đổ 3D, tự động hiển thị tiêu đề và phụ đề từ kịch bản của mọi slot.
  + Căn chỉnh sớ cuộn kết luận đáy Cảnh 1 ($y \in [1725, 1875]$): không còn lem nét vẽ minh họa bên trên.
  + Re-render hoàn tất video 2K Day 1 Slot 03 (53.4s, 78.24 MB) xuất tự động sang Google Drive `G:\My Drive\Đăng video\Day_01_Slot_03_Mẹo_Tăng_Độ_Thô_Không_Nôn_Trớ_Ngày_1_2K.mp4` và đồng bộ Sheets webhook thành công.
The above content does NOT show the entire file contents. If you need to view any lines of the file which were not shown to complete your task, call this tool again to view those lines.
- `TASK-028` — Khắc phục dứt điểm va chạm Title & Tag, giải phóng toàn bộ tranh minh họa doodle đáy và Chuẩn hóa Quy chuẩn Negative Space Architecture + Prompt GPT cho toàn bộ 330 Slot:
  + Sửa triệt để va chạm chữ trong thẻ bước compact: Trong `draw_step_pill_badge` (`whiteboard_app/art_shapes.py`), chuẩn hóa kích thước tag pill (`f_tag=18`, `tag_h=28`) và tính toán `gap_to_tag` an toàn, co giãn font tiêu đề bước tự động (`f_title=24` -> `16`), mở rộng thẻ card lên 430-440px trong `whiteboard_app/slot_builder.py`. Cảnh 3 hiển thị thông thoáng 100%, không còn bất kỳ ký tự nào đè lên nhau.
  + Giải phóng hoàn toàn tranh doodle đáy Cảnh 4: Đẩy khối CTA capsule lên $y \in [1500, 1650]$, giúp hình trái tim và quả dâu tây ở $y \in [1680, 1850]$ lộ diện trọn vẹn 100%, không bị che khuất.
  + Thiết lập Quy chuẩn Bố cục Negative Space Architecture & Bộ Prompt GPT mẫu (`knowledge/an_dam_me_dau/PROMPT_TEMPLATES_GPT.md`): Phân bổ chính xác các vùng cấm vẽ (Safe Zones / Negative Space) cho 4 cảnh: dải trên $y < 180$ cho Banner, $y \in [180, 500]$ Cảnh 1 cho thẻ cảnh báo, $y \in [880, 1060]$ Cảnh 2 cho thẻ xanh, bố cục 2 cột so le Zigzag Cảnh 3, và dải $y \in [1050, 1660]$ Cảnh 4 cho 3 huy hiệu + CTA. Đảm bảo bất kỳ ai tạo ảnh bằng GPT cũng không bao giờ bị lỗi đè chữ khi render hàng loạt.
  + Re-render hoàn tất video 2K Day 01 Slot 02 (1440x2560 30FPS, 114.19 MB, 83.9s) xuất tự động sang Google Drive `G:\My Drive\Đăng video\Day_01_Slot_02_Gạo_Tẻ_Nấu_Cháo_Rây_Bé_Mấy_Tháng_Ăn_Được_2K.mp4` và đồng bộ Sheets webhook thành công.
- `TASK-029` — Mở rộng Kế hoạch 330 Video với 8 cột Prompt & Chuẩn hóa Quy tắc Đặt tên File Ảnh GPT (`day_{DD}_slot_{SS}_scene_{CC}.jpg`):
  + Cập nhật `CONTENT_PLAN_30_DAYS_330_VIDEOS.csv` và `.json` lên 22 cột hoàn chỉnh: bổ sung cặp `file_name_scene_X` và `prompt_scene_X` cho toàn bộ 4 cảnh trong cả 330 slot (tổng cộng 1.320 prompt ảnh chuyên biệt tuân thủ tuyệt đối Negative Space Architecture).
  + Ban hành nguyên tắc đặt tên file ảnh bất biến: `day_{DD}_slot_{SS}_scene_{CC}.jpg` (định dạng 2 chữ số như `day_01_slot_02_scene_01.jpg`), tránh nhầm lẫn dữ liệu khi sinh và nạp hàng loạt.
  + Cập nhật System Prompt cho Custom GPT (`agents/an_dam_me_dau.agent.md`) và cẩm nang hướng dẫn (`knowledge/an_dam_me_dau/PROMPT_TEMPLATES_GPT.md`) để GPT tự động đọc repo GitHub và tạo ảnh chuẩn từng ngày.
  + Nâng cấp động cơ `scripts/generate_lively_slot.py` tự động nhận diện và nạp ảnh GPT chuẩn tên từ `projects/day_{DD}_slot_{SS}_golden/raw_gpt_images/`.
  + Xây dựng bộ mã Apps Script đồng bộ 1 chạm lên Google Sheets (`scripts/auto_import_to_google_sheet.js` và `scripts/google_apps_script_auto_sync.js`).
  + 70/70 unit tests PASS 100%.
- `TASK-030` — Đồng bộ toàn bộ 1.320 Prompt tạo ảnh của 330 Slot lên Google Sheets:
  + Nạp toàn bộ 330 video x 4 cảnh = 1.320 prompt ảnh và 1.320 tên file chuẩn lên Google Sheet thực tế qua Webhook Gateway `action: reset_all`.
  + Trang tính đã mở rộng lên 22 cột hoàn chỉnh, hiển thị đầy đủ thông tin kịch bản, hashtag và prompt tạo ảnh.
  + Kiểm tra live export thành công: 331 dòng (1 header + 330 rows) hiển thị đầy đủ 22 cột.
  + Trạng thái kỹ thuật: TECHNICALLY_VERIFIED (70/70 unit tests pass).

## Backlog ưu tiên

### `TASK-002` — Baseline test SRT và môi trường

- Thêm fixture SRT và test parser BOM/timestamp/lỗi.
- Compile/smoke check toàn repo.

### `TASK-003` — Annotation đa nền tảng

- Bỏ font hard-code.
- Thêm validator annotation chi tiết và lỗi tiếng Việt.

### `TASK-007` — Nghiệm thu app MVP trên Windows

- Người dùng chạy `run_app.bat`.
- App đã mở thành công; lỗi hộp chọn dự án mở hai lần đã được sửa trên branch.
- Lỗi `UnicodeEncodeError` do renderer dùng Windows `cp1252` đã được sửa bằng môi trường UTF-8 cho subprocess.
- Đã bổ sung dự án nội dung thật về 5 món bò cho bé để nghiệm thu màu, timing và audio.
- Phiên bản 2 chuyển sang ảnh món ăn bán chân thực, voice Việt neural và nhãn bút `Ăn dặm mẹ Dâu`.
- Phiên bản 3 sửa đúng yêu cầu nghiệm thu: bỏ nhãn nổi, thay chữ Trung Quốc ngay trên thân bút.
- Mở gói demo, render và kiểm tra `final.mp4`.
- Ghi nhận ảnh lỗi, log và trải nghiệm thao tác.
- Kiểm tra resize cửa sổ ở 1280×820 và kích thước nhỏ; các card không chồng nhau.
- Kiểm tra một video 9:16 và luồng chọn voice có sẵn.
- Khi có OmniVoice sẵn, chọn CLI một lần và xác nhận lần mở app sau vẫn nhớ đường dẫn.
- Xác nhận app lấy thẳng `script.txt`, không yêu cầu copy lời thoại vào giao diện.
- Thêm một mẫu giọng thật, nghe trước/sau xử lý và đánh giá mức nhiễu còn lại hoặc méo tiếng.
- Chạy gói bò v6, xác nhận 5 câu khớp 5 vùng hình; ghi nhận offset và độ rõ âm đầu cần tinh chỉnh.
- Xác nhận cột trái hiện đủ 5 phân cảnh dù gói chỉ dùng một ảnh tổng.
- Xác nhận một lần bấm **Tạo video** tự chạy voice, timeline, render và mở được preview kết quả.
- Xác nhận player nội bộ phát tiếng, tua không lệch hình và nút ↗ mở ngoài khi cần.
- Nghe riêng đầu 5 cue, xác nhận “thứ nhất/hai/ba/tư/năm” không nhỏ hoặc hụt.
- Nạp năm ZIP tại `examples/multi-job-5-pack/zips/`, chạy toàn bộ và xác nhận job sau tự tiếp tục khi job trước hoàn tất hoặc lỗi.

### `TASK-008` — Tự tạo annotation từ scene

- Sinh region/timing cơ bản từ ảnh và metadata cảnh.
- Cho phép chỉnh trước khi render.

### `TASK-009` — Đồng bộ ChatGPT

- Chốt cơ chế MCP/backend sau khi schema v1 ổn định.
- Nhận phiên bản dự án mới mà không copy từng file.
- Báo tiến độ render trở lại ChatGPT.

### `TASK-006` — Render verification tự động

- Fixture ảnh + annotation nhỏ.
- Kiểm tra first/mid/final frame và duration.

### `TASK-010` — Multi-job bền vững

- Trạng thái: `READY_FOR_USER_TEST`; chi tiết tại `docs/MULTI_JOB_DESIGN.md`.
- M2A: đã thêm phase/progress cho pipeline và giữ nguyên luồng đơn nhiệm.
- M2B: đã có SQLite queue, một worker tuần tự, dashboard, hủy/thử lại và recovery.
- UI: dashboard ba cột responsive gồm hàng đợi thu gọn, kịch bản riêng, preview/tiến độ và log theo job.
- Thiết lập video dùng popup cho một hoặc nhiều checkbox; áp dụng đồng loạt nhưng vẫn cô lập output theo `job_id`. Job queued/running bị khóa; job hoàn tất/lỗi/đã hủy được đưa về chờ để chạy lại.
- Checkbox tiêu đề chọn/bỏ chọn toàn bộ job đang hiển thị và phản ánh trạng thái chọn một phần/toàn bộ.
- Nút Thiết lập N job nằm cạnh Chạy N job; cấu hình OmniVoice nhập tay và giọng được chọn được lưu bền vững qua lần mở app tiếp theo.
- Preview trong Đơn nhiệm và Multi Job bám theo tỷ lệ đầu ra đã chọn/lưu thay vì giữ nguyên tỷ lệ ảnh nguồn.
- Popup thiết lập preview live theo tỷ lệ, nhớ lựa chọn gần nhất; queue cũ không được tự chạy khi mở app.
- Preview có nhãn tỷ lệ, voice mặc định tự chọn lại và nút chạy hiển thị trạng thái cùng thời gian đã chạy.
- Bảng job có cột Voice/Khung hình; voice snapshot cũ được ánh xạ lại về profile thư viện.
- M2C còn lại: worker OmniVoice sống lâu, cache cue theo nội dung và resume theo phase.
- M2D: chỉ tăng render concurrency sau benchmark; không chạy nhiều model voice đồng thời.
