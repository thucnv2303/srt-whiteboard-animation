# Nhật ký quyết định

## DEC-20260906-08 — Khắc phục Va Chạm Title/Tag, Giải Phóng Doodle Đáy và Chuẩn Hóa Quy Chuẩn Negative Space + Prompt GPT Cho 330 Slot
- Status: approved
- Decision owner: người dùng
- Context: Khung chữ bị tràn viền và va chạm giữa tiêu đề bước với tag viên thuốc ở Cảnh 3; khối CTA ở Cảnh 4 đặt quá thấp đè lên hình vẽ doodle trái tim và dâu tây; các ảnh tạo bằng GPT cần có quy chuẩn vùng trống (Negative Space) rõ ràng để khi chạy hàng loạt cho mọi slot không bao giờ bị chữ đè ảnh.
- Decision:
  1. Tinh chỉnh thuật toán `draw_step_pill_badge`: với thẻ compact (< 600px), chuẩn hóa tag pill font 18px / height 28px, tính toán khoảng đệm an toàn `gap_to_tag` và tự động co giãn font tiêu đề bước (`f_title` từ 24px xuống tối thiểu 16px).
  2. Bổ sung hàm `wrap_text` tự động ngắt dòng thông minh theo từ cho toàn bộ các khối chữ mô tả, bảo đảm 100% chữ không bao giờ tràn viền card.
  3. Cảnh 4: Đẩy khối CTA capsule lên $y \in [1500, 1650]$, giải phóng hoàn toàn vùng $y \in [1680, 1850]$ cho doodle trái tim và quả dâu tây.
  4. Ban hành bộ quy chuẩn kiến thức `PROMPT_TEMPLATES_GPT.md` định nghĩa 4 vùng Negative Space bất biến trên canvas 1080x1920 cho 4 cảnh và checklist 5 tiêu chí kiểm định ảnh trước khi render.
- Files affected: `whiteboard_app/art_shapes.py`, `whiteboard_app/slot_builder.py`, `knowledge/an_dam_me_dau/PROMPT_TEMPLATES_GPT.md`, `.ai/CURRENT_CONTEXT.md`, `.ai/TASKS.md`.

## DEC-20260906-07 — Chuẩn hóa 5 Khối Đồ họa Nghệ thuật, Auto-Fit Padding chống đè chữ/icon và Sổ bộ Chủ đề Đã Duyệt
- Status: approved
- Decision owner: người dùng
- Context: Khung chữ nhật đơn điệu; xuất hiện lỗi chữ đè lên viền mép dải ruy băng và icon trái tim đè lên chữ CTA; cần phân định minh bạch các chủ đề người dùng đã duyệt thành công làm tiêu chuẩn vàng (Golden Benchmark) để không bị nhầm lẫn khi sản xuất hàng loạt.
- Decision:
  1. Thay thế 100% khung chữ nhật bằng 5 khối đồ họa nghệ thuật: 3D Swallowtail Ribbon Banner (tiêu đề), Comic Speech Bubble (cảnh báo chỉ nhân vật), Washi Memo Card (cơ chế/lời khuyên), Circular Stamp Badges ❶ ❷ ❸ + Pill Tags (3 bước thực hành), Capsule Heart CTA (kêu gọi hành động).
  2. Triển khai thuật toán Auto-Fit padding an toàn: Tự động đo `textbbox`, co giãn font size đảm bảo lề đệm >= 60px trong ruy băng; icon tim cách chữ >= 40px; tiêu đề bước không chạm tag viên thuốc.
  3. Thiết lập Sổ bộ Chủ đề Đã Duyệt (`.ai/APPROVED_TOPICS.md` & `knowledge/an_dam_me_dau/APPROVED_TOPICS.json`): Chỉ ghi nhận các chủ đề người dùng ĐÃ DUYỆT THÀNH CÔNG (Hiện tại gồm Day 01 Slot 01 và Day 01 Slot 02 - Golden Benchmark); toàn bộ các chủ đề khác được đánh dấu `PENDING_STANDARDIZATION`.
- Files affected: `scripts/build_day01_slot02_lively.py`, `.ai/APPROVED_TOPICS.md`, `knowledge/an_dam_me_dau/APPROVED_TOPICS.json`, `knowledge/an_dam_me_dau/KNOWLEDGE_BASE.md`, `agents/an_dam_me_dau.agent.md`.

## DEC-20260905-06 — Chuẩn hóa Typography lớn, loại bỏ Whoosh SFX, chuyển trang Slide và vẽ từ trên xuống dưới
- Status: approved
- Decision owner: người dùng
- Context: Thẻ chữ nhỏ khó đọc trên thiết bị di động 9:16; âm Whoosh gây gắt tai; hiệu ứng chuyển cảnh cần giống thao tác lật/chuyển trang; thứ tự nét vẽ cần tôn trọng quán tính thị giác từ trên xuống dưới.
- Decision:
  1. Typography: bắt buộc font size tối thiểu 36px cho body, 42-46px cho title/key badge; làm sạch unicode emoji thô.
  2. Bỏ hoàn toàn âm thanh chuyển cảnh Whoosh SFX trong `whiteboard_app/timeline.py`.
  3. Cập nhật hiệu ứng chuyển cảnh sang `slideleft` (0.35s) mô phỏng chuyển trang tự nhiên.
  4. Chuẩn hóa thuật toán vẽ nét `cluster_ink_streams` sắp xếp theo tọa độ $y$ tăng dần (từ trên xuống dưới).
- Files affected: `whiteboard_app/timeline.py`, `whiteboard_app/renderer.py`, `scripts/merge_scenes.py`, `scripts/stream_render.py`.

## DEC-20260831-01 — Codex trực tiếp triển khai

- Status: approved
- Decision owner: người dùng
- Context: Bộ luật cũ đặt ChatGPT ở vai trò supervisor và Anti/OpenCode/Kiro/Codex ở vai trò executor.
- Decision: Codex trực tiếp đọc code, sửa code, chạy kiểm tra, quản lý branch/commit/PR và cập nhật tài liệu. Không mặc định giao code cho Anti hoặc executor trung gian.
- Reason: Người dùng muốn làm việc trực tiếp với Codex trên GitHub và chỉ tập trung chạy app, kiểm tra kết quả, đưa ý tưởng.
- Trade-offs: Codex phải tự duy trì bằng chứng kỹ thuật và trạng thái repository rõ ràng; người dùng vẫn là người nghiệm thu hành vi thực tế.
- Files affected: `AGENTS.md`, `START_HERE.md`, toàn bộ `.ai/`.

## DEC-20260831-02 — Người dùng là quyền nghiệm thu sản phẩm cuối

- Status: approved
- Decision owner: người dùng
- Context: Kiểm tra tự động không chứng minh trải nghiệm app đã đúng ý tưởng.
- Decision: Codex có thể xác nhận kiểm tra kỹ thuật; trạng thái chấp nhận sản phẩm cần kết quả chạy app của người dùng.
- Reason: Người dùng là người vận hành và đánh giá đầu ra hình ảnh/video.
- Trade-offs: Một task có thể ở trạng thái `READY_FOR_USER_TEST` dù toàn bộ test tự động đã pass.

## DEC-20260831-03 — Dùng upstream làm nền, phát triển ở repo riêng

- Status: approved
- Decision owner: người dùng + Codex
- Context: Repo `geeklee/srt-whiteboard-animation` là public nhưng tài khoản `thucnv2303` chỉ có quyền đọc.
- Decision: Duy trì upstream để tham chiếu; mọi thay đổi dự án thực hiện trên fork `thucnv2303/srt-whiteboard-animation`.
- Reason: Có quyền kiểm soát branch, PR và roadmap mà không thay đổi trực tiếp repo của tác giả.
- Trade-offs: Cần chủ động đồng bộ upstream và xử lý conflict khi lấy bản mới.

## DEC-20260831-04 — Tiếng Việt là ngôn ngữ sản phẩm

- Status: approved
- Decision owner: người dùng
- Context: Upstream dùng tiếng Trung trong tài liệu, log và UI.
- Decision: UI, hướng dẫn và thông báo lỗi dành cho người dùng phải dùng tiếng Việt; code identifier có thể giữ tiếng Anh.
- Reason: Người dùng chính làm việc bằng tiếng Việt.
- Trade-offs: Cần rà soát chuỗi hiển thị và giữ tài liệu upstream khi cần đối chiếu.

## DEC-20260831-05 — Tách sáng tạo khỏi renderer

- Status: approved
- Decision owner: người dùng
- Context: Người dùng muốn ChatGPT Project tạo ý tưởng, kịch bản, voice và ảnh chất lượng cao mà không chạy AI local.
- Decision: ChatGPT là studio sáng tạo; app local chỉ nhận gói dự án chuẩn, kiểm tra, preview và dựng video.
- Trade-offs: Cần hợp đồng dữ liệu ổn định và một cầu đồng bộ ở milestone sau.

## DEC-20260831-06 — Desktop Windows trước

- Status: approved
- Decision owner: Codex theo môi trường mục tiêu đã chốt
- Decision: MVP dùng Python/Tkinter, bọc renderer hiện có, không viết lại engine và không thêm framework UI nặng.
- Reason: Chạy local, phù hợp FFmpeg/Python hiện tại, có thể đóng gói `.exe` sau.
- Trade-offs: Giao diện MVP thiên về vận hành; preview nâng cao và installer làm sau nghiệm thu.

## DEC-20260831-07 — Gói dự án schema v1

- Status: approved
- Decision owner: người dùng + Codex
- Decision: Đầu vào là folder/ZIP có đúng một `project.json`; mỗi scene tham chiếu ảnh và annotation cùng basename; voice tùy chọn.
- Security: Chỉ cho đường dẫn tương đối nằm trong root; từ chối ZIP traversal và tài nguyên thiếu.

## DEC-20260901-01 — Voice neural không API key cho bước nghiệm thu

- Status: approved for testing
- Decision owner: người dùng + Codex
- Context: Windows SAPI đọc tiếng Việt sai hoặc rơi về voice không phải tiếng Việt.
- Decision: Gói mẫu dùng edge-tts với `vi-VN-HoaiMyNeural`; app vẫn chỉ nhận file audio và không phụ thuộc dịch vụ TTS khi render.
- Trade-offs: Không tốn API key nhưng cần Internet khi tạo voice; có thể thay bằng voice do ChatGPT Project xuất sau này.

## DEC-20260901-02 — Nhãn bút là dữ liệu dự án

- Status: approved
- Decision owner: người dùng
- Decision: Schema v1 cho phép trường tùy chọn `penBrand`; renderer dùng Pillow để xóa chữ Trung Quốc rồi ghi chữ Việt trực tiếp lên thân bút mặc định.
- Reason: Đổi tên thương hiệu theo từng dự án mà không sửa file ảnh nguồn.

## DEC-20260901-03 — UI ngang responsive và đơn nhiệm

- Status: approved
- Decision owner: người dùng
- Decision: Màn hình mặc định dùng bố cục ngang gồm preview bên trái, thiết lập bên phải, dải cảnh và card log toàn chiều ngang ở đáy. App chỉ chạy một tác vụ tại một thời điểm; khi cửa sổ hẹp, thiết lập chuyển xuống dưới preview.
- Reason: Phù hợp màn hình máy tính, giảm mục dư thừa và vẫn dùng được khi thay đổi kích thước cửa sổ.

## DEC-20260901-04 — Tái sử dụng OmniVoice bên ngoài repo

- Status: approved
- Decision owner: người dùng + Codex
- Decision: App cho chọn file voice hoặc gọi `omnivoice-infer.exe` từ môi trường OmniVoice đã tồn tại. Chỉ lưu đường dẫn CLI trong `%APPDATA%`, không clone source, môi trường hay model vào repo.
- Reason: Tránh tốn dung lượng và tránh duy trì nhiều bản OmniVoice trên cùng máy.

## DEC-20260901-05 — GPT không xuất voice

- Status: approved
- Decision owner: người dùng
- Decision: Gói GPT chỉ chứa ảnh, annotation và `script.txt`. Sau khi quét gói, cột phải hiển thị metadata và kịch bản; app bắt buộc tạo audio local bằng OmniVoice trước khi bật nút dựng video.
- Reason: Kịch bản và hình ảnh cần đồng bộ từ GPT, còn voice clone dùng tài nguyên/giọng mẫu riêng đã có trên máy người dùng.

## DEC-20260901-06 — Thư viện giọng và popup cài đặt

- Status: approved
- Decision owner: người dùng
- Decision: Màn hình chính chỉ hiển thị danh sách giọng đã lưu, nghe thử và tạo audio. Đường dẫn engine, thêm giọng clone và xử lý mẫu nằm trong popup **Cài đặt giọng**. Voice profile dùng chung cho mọi dự án.
- Audio pipeline: tự chọn đoạn nói liên tục 3–8 giây theo mức năng lượng/SNR, xuất WAV mono 24 kHz, high-pass 80 Hz, low-pass 8 kHz, FFT denoise, dynamic normalize và limiter.
- Constraint: Không tuyên bố xóa tuyệt đối mọi loại tạp âm; người dùng phải nghe thử bản xử lý trước khi dùng để clone.

## DEC-20260902-01 — Audio là đồng hồ của timeline

- Status: approved
- Decision owner: người dùng
- Decision: GPT cung cấp `narration[]` với cue, `sceneId` và `elementIds`. OmniVoice tạo từng cue trong một lần nạp model; app đo thời lượng WAV thật rồi sinh timeline và annotation runtime. Không kéo/cắt voice để ép vào duration hình cố định.
- Timing defaults: vẽ bắt đầu sau voice 100 ms, hoàn tất trước cuối cue khoảng 500 ms, nghỉ mặc định 200–250 ms và giữ hình 500 ms cuối cảnh.
- Source safety: không ghi đè annotation từ GPT; renderer chỉ dùng file trong `output/runtime-annotations/` cho lần dựng hiện tại.

## DEC-20260902-02 — Pipeline một nút và cue là phân cảnh UI

- Status: approved
- Decision owner: người dùng
- Decision: Màn hình chính chỉ có một hành động **Tạo video**, tự chạy tạo voice, đồng bộ timeline, render và ghép MP4. Narration cue được hiển thị như phân cảnh nội dung, kể cả khi nhiều cue dùng chung một ảnh nguồn.
- Preview: Sau khi dựng xong, app tạo `preview.jpg`, chuyển cột trái sang chế độ video kết quả và mở `final.mp4` bằng trình phát mặc định khi người dùng bấm phát.
- Reason: Giảm thao tác thủ công, hiển thị đúng cấu trúc nội dung mà người dùng cần kiểm tra và dành thêm không gian cho thông tin dự án.

## DEC-20260902-03 — Trình phát video tích hợp

- Status: approved
- Decision owner: người dùng
- Decision: Phát MP4 trực tiếp trong canvas Tkinter bằng PyAV; FFmpeg trích WAV PCM và pygame phát từ đúng offset khi tua. Âm thanh là clock, player bỏ frame trễ để hạn chế lệch tiếng/hình.
- Controls: phát/tạm dừng, dừng, thanh tua, thời gian hiện tại/tổng và nút mở ngoài dự phòng.
- Dependency: `run_app.bat` luôn chạy kiểm tra môi trường để tự bổ sung pygame cho `.venv` cũ; không yêu cầu người dùng clone/cài lại dự án.
- Windows audio: mixer chạy cố định 48 kHz stereo; audio nguồn 24 kHz mono được đóng gói WAV có header để SDL tự resample. Không truyền raw PCM vì thiết bị có thể đổi sample rate và làm tiếng nhanh/méo.
- Video sync: audio/monotonic clock là chuẩn; frame 60 fps đã trễ bị bỏ thay vì phát bù, tránh hình tụt dần sau tiếng trên canvas Tkinter.

## DEC-20260902-04 — Bảo vệ âm đầu narration cue

- Status: approved
- Decision owner: người dùng
- Evidence: Trong video nghiệm thu, 100 ms đầu của “Hai/Ba/Bốn” thấp hơn phần thân câu khoảng 5–6 dB dù cue không bị cắt ở bước ghép.
- Decision: Thêm dấu chấm lửng làm token đệm không lời trước text tổng hợp; hậu xử lý từng WAV bằng onset boost thích ứng tối đa 5,1 dB, release ngắn, soft peak và 60 ms leading pad. Timeline tiếp tục đo file sau xử lý nên không mất đồng bộ.
- Copy rule: Với danh sách, ưu tiên “Món thứ hai là…” thay cho cue bắt đầu trơ bằng “Hai, …”; số quan trọng không nên là token đầu tuyệt đối của một lần sinh TTS.

## DEC-20260902-05 — Multi-job dùng queue tuần tự trước concurrency

- Status: implemented, ready for Windows acceptance
- Decision owner: Codex, chờ người dùng nghiệm thu từng milestone
- Context: App cần nhận nhiều dự án nhưng OmniVoice dùng GPU, renderer có file trung gian và UI Tkinter không an toàn khi nhiều worker cập nhật trực tiếp.
- Decision: Lưu queue bằng SQLite, snapshot cấu hình mỗi job, cô lập output theo `job_id` và dùng một `JobRunner` tuần tự ở M2B. OmniVoice là một worker sống lâu và chỉ xử lý một tác vụ TTS mỗi lúc.
- Recovery: Job đang chạy khi app tắt chuyển thành `INTERRUPTED`; retry dùng lại artifact hợp lệ theo phase. File hoàn chỉnh chỉ được công bố bằng đổi tên nguyên tử.
- Concurrency: Chỉ cho render song song có giới hạn sau benchmark máy thật; không mặc định nạp nhiều model voice.
- Reason: Có ngay lợi ích xếp hàng nhiều dự án mà không đánh đổi tính ổn định, khả năng hủy và tính toàn vẹn kết quả.
- Implementation: `whiteboard_app/jobs.py` lưu SQLite và chạy `SequentialJobRunner`; `whiteboard_app/multi_job_ui.py` cung cấp dashboard KPI/filter/checkbox/retry. Mỗi job ghi vào `output/runs/<job_id>/`.

## DEC-20260902-06 — Dashboard ba cột và thiết lập hàng loạt

- Status: approved
- Decision owner: người dùng
- Decision: Multi Job dùng ba cột trên màn hình rộng: hàng đợi thu gọn, kịch bản riêng và preview/tiến độ. Checkbox là phạm vi của popup thiết lập; không có checkbox thì chỉ sửa job đang xem.
- Output safety: Khi áp dụng cho nhiều job, nơi lưu là thư mục gốc và app tự thêm thư mục con theo `job_id`; không cho nhiều job ghi chung một output.
- Locking: Job queued/running không đổi snapshot; các job còn lại nhận cấu hình và chuyển về waiting nếu cần chạy lại.

## DEC-20260905-01 — Scene-Level Seamless Voice & Keyword Alignment Timeline

- Status: approved & implemented
- Decision owner: người dùng + Codex
- Context: Chia nhỏ kịch bản thành 9–10 narration cue vụn (2–5s) khiến TTS nạp/ngắt quãng liên tục, dễ sinh tạp âm "hờ/ồ" ở đầu mỗi câu và khiến người dùng lo ngại hình ảnh lệch pha với âm thanh nếu chỉ phân bổ mù.
- Decision:
  1. Gom toàn bộ kịch bản theo từng Cảnh (`scene_id`); OmniVoice chỉ sinh 1 file voice liền mạch cho mỗi cảnh trong 1 lần nạp model duy nhất.
  2. Tự động căn chỉnh tốc độ vẽ tay (Adaptive Reveal Timing) theo độ dài voice thực tế của cảnh, dành 650–700ms tĩnh (gaze pause) cuối cảnh để ngắm tranh hoàn chỉnh trước khi chuyển cảnh.
  3. Đồng bộ ngữ nghĩa (Keyword Alignment): Sử dụng Whisper word-timestamps để phát hiện thời điểm phát âm chính xác của các câu/từ khóa trong cảnh, gán `reveal.startMs` của phần tử đúng vào thời điểm đó (kèm fallback mượt mà theo trọng số độ dài ký tự).
- Implementation: `generate_scene_voices` trong `whiteboard_app/voice.py`, `compile_scene_timeline` & `detect_cue_offsets_in_scene` trong `whiteboard_app/timeline.py`, tích hợp vào `ui.py` và `jobs.py`.

## DEC-20260905-02 — Hiệu ứng chuyển cảnh xfade, Typography chuẩn HD và Whoosh SFX

- Status: approved & implemented
- Decision owner: người dùng + Codex
- Context: Video ghép các cảnh bị đơ nhịp do gaze_ms quá dài (700ms) và cắt cứng (hard-cut); chữ trên ảnh li ti khó đọc và bị lỗi ký tự ô vuông unicode trên Windows; thiếu hiệu ứng âm thanh minh họa nét vẽ và chuyển cảnh.
- Decision:
  1. Rút ngắn thời gian tĩnh cuối cảnh `gaze_ms` về 250ms, ăn khớp hoàn hảo với thời lượng hiệu ứng chuyển cảnh `wipeleft 0.25s`.
  2. Bổ sung bộ lọc `xfade` kết hợp phần cứng GPU MFT (`h264_mf`) trong `scripts/merge_scenes.py` và gọi từ `whiteboard_app/renderer.py`, tạo hiệu ứng lướt gạt cảnh mượt mà.
  3. Tái thiết kế toàn bộ thẻ chữ trên ảnh nguồn: cỡ chữ 44-52px font Arial Bold tương phản cao, định dạng Badge & Keyword to bản, xóa sạch chữ con li ti và loại bỏ emoji ký tự unicode gây lỗi ô vuông `□`.
  4. Tích hợp Whoosh SFX (`assets/whoosh.wav`) vào timeline audio tại mốc chuyển tiếp giữa các cảnh (`global_cursor - 120ms`) với âm lượng cân bằng (0.6), tăng tính sinh động và kích thích thị giác/thính giác người xem.
- Implementation: `scripts/merge_scenes.py`, `whiteboard_app/renderer.py`, `whiteboard_app/timeline.py`, tài nguyên `assets/whoosh.wav`, `assets/scribble.wav`.

## DEC-20260905-03 — Nâng cấp độ phân giải 2K / 4K, đồng bộ màu canvas và thương hiệu thân bút

- Status: approved & implemented
- Decision owner: người dùng + Codex
- Context: Video xuất ra bị mờ hạt, vỡ nét, lem màu và giật màu ở frame tĩnh cuối cảnh; thân bút chưa xóa được chữ gốc khi `pen_brand` rỗng; người dùng yêu cầu nâng chất lượng video lên chuẩn 2K / 4K sắc nét và sinh động.
- Decision:
  1. Mở rộng preset độ phân giải: Hỗ trợ các chuẩn `16:9 (720p / 2K / 4K)`, `9:16 (1080p / 2K 1440x2560 / 4K 2160x3840)`, `1:1 (1080p / 2K)`.
  2. Đồng bộ màu nền canvas khởi tạo: Tự động trích xuất màu nền thực tế của ảnh nguồn (lấy median 4 biên ngoài) gán cho `canvas_bgr` khi không `match_bg`, loại bỏ hoàn toàn viền răng cưa và hiện tượng giật màu nhấp nháy giữa các vùng bounding box và frame kết thúc.
  3. Co giãn kích thước bàn tay: Tự động tính tỷ lệ bàn tay `target_hand_height` theo chiều cao khung hình `out_h` (chuẩn 493px ở 1080p -> 657px ở 2K), giúp nét vẽ và bàn tay giữ tỷ lệ tự nhiên, sinh động, không bị teo nhỏ trên độ phân giải siêu nét.
  4. Luôn kích hoạt thương hiệu thân bút: Fallback `project.pen_brand or "Ăn dặm mẹ Dâu"` để bảo đảm 100% video xuất ra đều được xóa sạch chữ Trung Quốc gốc và in chữ thương hiệu sắc nét.
  5. Tối ưu bitrate encoder: Nâng mức bitrate cho hardware encoder `h264_mf` lên `-b:v 15M` và `libx264` lên `-crf 18 -preset veryfast`, bảo toàn từng chi tiết sắc nét của nét vẽ và màu sắc.
## DEC-20260905-04 — Bộ ảnh Visual Storytelling hoạt hình, Bounding Box 100% độ phủ và thuật toán trim_leading_hallucination

- Status: approved & implemented
- Decision owner: người dùng + Codex
- Context:
  1. Cảnh 3 bị cắt cụt nửa dưới do `height: 250` không bao trọn nội dung hình ảnh thực tế (cao 585px).
  2. Giọng OmniVoice bị lặp âm rác/hallucination ("đỏ", "dễ ăn", "để ăn") trước mỗi câu do file audio mẫu reference bị cắt lửng lơ ở đuôi.
  3. Bộ ảnh minh họa cũ thiếu sức hút, chưa sinh động và thiếu tính kể chuyện trực quan.
- Decision:
  1. Tái tạo bộ 4 ảnh hoạt hình thiếu nhi ấm áp bằng ImageGen (Children's book comic doodle sketch), nét phác xám trên nền kem `#F5EBD7`, giàu biểu cảm nhân vật (bé háo hức, quả thận ngộ nghĩnh nâng tạ, dạ dày êm ái trôi trên sóng sữa mẹ).
  2. Tối ưu cấu trúc `annotation.json`: chia dải Y liên tục phủ kín $100.0000\%$ diện tích canvas (0 pixel bị bỏ sót), giải quyết dứt điểm lỗi cắt cụt chi tiết.
  3. Xử lý triệt để hallucination âm thanh:
     - Gọt tỉa chính xác file mẫu reference `62f4aecdb5fa4ad3b7edbc49865d5b9a.wav` tại 2.80s (fade-out 30ms + đệm 150ms silence).
     - Bổ sung hàm `trim_leading_hallucination` trong `whiteboard_app/voice.py` tự động đối chiếu kịch bản bằng Whisper word timestamps; tự động gọt sạch mọi âm phantom trước từ khóa đầu tiên của câu thoại.
- Implementation: `whiteboard_app/voice.py`, `projects/day_01_an_dam_v2/scene_*.png`, `projects/day_01_an_dam_v2/scene_*.annotation.json`, `scripts/render_day01_v2.py`.

## DEC-20260905-05 — Phân tách độc lập thẻ chữ, kịch bản voice y khoa cặn kẽ và thư thái nhịp xem (84.6s, gaze 1000ms)

- Status: approved & implemented
- Decision owner: người dùng + Codex
- Context:
  1. Thẻ chữ Bước 2 bị hổng từ, mất nét do hình minh họa (nồi cháo) và thẻ chữ bị gộp chung vào 1 element trong `annotation.json`; giải thuật vẽ nhảy qua lại giữa nét vẽ nồi và chữ.
  2. Người dùng phản hồi xem bị "đuổi", chuyển cảnh quá nhanh chưa kịp tiếp nhận thông tin (trước đó 4 cảnh chỉ có 42.7s, cảnh công thức chỉ có 9s).
  3. Kịch bản voice cũ nói chung chung, thiếu sự cặn kẽ, cụ thể và thuyết phục của chuyên gia dinh dưỡng y khoa.
- Decision:
  1. Phân tách rạch ròi 100% hình minh họa và thẻ chữ thành các element độc lập trong `annotation.json`. Mỗi thẻ chữ và mỗi hình vẽ có bounding box chuẩn xác và thời điểm vẽ riêng.
  2. Nâng cấp `classify_stroke_groups` và `_chain_region_paths` trong `scripts/stream_render.py`: nhận diện đúng dải mật độ chữ Latin (0.04 - 0.65), phạt nặng bước nhảy ngược dòng (`dr < -2`), bảo đảm thứ tự vẽ tự nhiên từ trên xuống dưới, trái sang phải, không bao giờ bỏ sót chữ giữa chừng.
  3. Viết lại kịch bản voice sâu sắc, cặn kẽ chuẩn chuyên gia: hướng dẫn chính xác gạo tẻ nguyên cám giàu vitamin B1, tỷ lệ vàng 10g gạo : 100ml nước, ninh nhỏ lửa 45 phút đậy vung kín, rây mắt nhỏ 0.5mm miết 2 lần, lượng 1-2 thìa cà phê ngày đầu và theo dõi dị ứng 3 ngày.
  4. Tăng thời lượng video lên 84.6s (Cảnh 1: 15.4s, Cảnh 2: 21.5s, Cảnh 3: 29.6s, Cảnh 4: 18.1s) và bổ sung 1.0s (1000ms) dừng tĩnh cuối mỗi cảnh trước khi lướt chuyển trang.
- Implementation: `scripts/stream_render.py`, `scripts/build_day01_slot02_lively.py`, `whiteboard_app/timeline.py`.
