# Nhật ký quyết định

## DEC-20260831-01 — Codex trực tiếp triển khai

- Status: approved
- Decision: Codex trực tiếp code, kiểm tra, quản lý branch/commit/PR; người dùng chạy app và nghiệm thu.

## DEC-20260831-02 — Người dùng nghiệm thu sản phẩm cuối

- Status: approved
- Decision: kiểm tra tự động xác nhận kỹ thuật; người dùng xác nhận trải nghiệm và video thực tế.

## DEC-20260831-03 — Dùng upstream làm nền

- Status: approved
- Decision: phát triển trên fork `thucnv2303/srt-whiteboard-animation`, giữ upstream để tham chiếu.

## DEC-20260831-04 — Tiếng Việt là ngôn ngữ sản phẩm

- Status: approved
- Decision: UI, hướng dẫn và lỗi dành cho người dùng dùng tiếng Việt.

## DEC-20260831-05 — Tách sáng tạo khỏi renderer

- Status: approved
- Decision owner: người dùng
- Context: Người dùng muốn ChatGPT Project tạo ý tưởng, kịch bản, voice và ảnh chất lượng cao mà không chạy AI local.
- Decision: ChatGPT là studio sáng tạo; app local chỉ nhận gói dự án chuẩn, kiểm tra, preview và dựng video.
- Trade-offs: cần hợp đồng dữ liệu ổn định và một cầu đồng bộ ở milestone sau.

## DEC-20260831-06 — Desktop Windows trước

- Status: approved
- Decision owner: Codex theo môi trường mục tiêu đã chốt
- Decision: MVP dùng Python/Tkinter, bọc renderer hiện có, không viết lại engine và không thêm framework UI nặng.
- Reason: chạy local, phù hợp FFmpeg/Python hiện tại, có thể đóng gói `.exe` sau.
- Trade-offs: giao diện MVP thiên về vận hành; preview nâng cao và installer làm sau nghiệm thu.

## DEC-20260831-07 — Gói dự án schema v1

- Status: approved
- Decision: đầu vào là folder/ZIP có đúng một `project.json`; mỗi scene tham chiếu ảnh và annotation cùng basename; voice tùy chọn.
- Security: chỉ cho đường dẫn tương đối nằm trong root; từ chối ZIP traversal và tài nguyên thiếu.

