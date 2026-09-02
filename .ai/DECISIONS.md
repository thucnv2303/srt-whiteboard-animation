# Nhật ký quyết định

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
