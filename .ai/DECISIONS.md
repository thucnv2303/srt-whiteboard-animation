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
