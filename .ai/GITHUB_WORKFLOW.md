# Quy trình GitHub

## Repository

- Upstream read-only: `geeklee/srt-whiteboard-animation`
- Repo làm việc: `thucnv2303/srt-whiteboard-animation`
- Remote đề xuất:
  - `origin`: repo của người dùng
  - `upstream`: repo của tác giả

## Branch

- Base: `main`
- Knowledge/bootstrap: `docs/bootstrap-project-knowledge`
- Feature: `feat/<ten-ngan>`
- Bug: `fix/<ten-ngan>`
- Test: `test/<ten-ngan>`
- Maintenance: `chore/<ten-ngan>`

## PR checklist

- Mục tiêu người dùng và phạm vi.
- Changed files và quyết định đáng chú ý.
- Lệnh kiểm tra + kết quả thực tế.
- Ảnh/video minh chứng khi có UI hoặc render.
- Rủi ro và backward compatibility.
- Hướng dẫn người dùng chạy app nghiệm thu.
- Không còn secret, artifact hoặc unrelated change.

## Merge

- Codex không tự merge chỉ vì CI pass.
- Sau khi người dùng nghiệm thu, Codex có thể merge nếu người dùng yêu cầu rõ và branch protection cho phép.
- Sau merge, cập nhật context/task và xóa branch nếu an toàn.

## Đồng bộ upstream

- Fetch upstream và xem diff trước khi nhập thay đổi.
- Dùng branch riêng cho mỗi lần sync.
- Không tự động ghi đè thay đổi bản địa hóa hoặc schema của dự án.
- Ghi quyết định nếu upstream thay đổi workflow/rendering đáng kể.
