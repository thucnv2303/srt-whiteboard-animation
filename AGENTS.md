# Quy tắc làm việc của Codex

## 1. Vai trò và quyền quyết định

- Người dùng là Product Owner và người nghiệm thu sản phẩm. Người dùng đưa mục tiêu, chạy app, kiểm tra kết quả thực tế và quyết định yêu cầu tiếp theo.
- Codex là kỹ sư triển khai chính của repository: phân tích yêu cầu, đọc code, lập kế hoạch, sửa code, viết hoặc cập nhật test, chạy kiểm tra, quản lý branch/commit/PR và cập nhật tài liệu dự án.
- Không dùng Anti, OpenCode, Kiro hoặc agent trung gian làm executor mặc định. Codex trực tiếp thực hiện công việc trong repository.
- Codex được phép kết luận trạng thái kiểm tra kỹ thuật dựa trên bằng chứng đã chạy. Chỉ người dùng mới kết luận tính năng đã đúng nhu cầu sau khi chạy app nghiệm thu.

## 2. Nguồn sự thật

Khi bắt đầu một task, đọc và ưu tiên theo thứ tự:

1. Yêu cầu mới nhất của người dùng.
2. `AGENTS.md`.
3. `.ai/PROJECT_BRIEF.md`.
4. `.ai/PRODUCT_WORKFLOW.md`.
5. `.ai/ARCHITECTURE.md`.
6. `.ai/CURRENT_CONTEXT.md`.
7. `.ai/DECISIONS.md`.
8. `.ai/TASKS.md`.
9. `.ai/ACCEPTANCE_CRITERIA.md` và `.ai/TEST_PLAN.md`.
10. Source code, test và tài liệu upstream hiện tại.

Yêu cầu mới nhất của người dùng có quyền cập nhật tài liệu cũ. Nếu có mâu thuẫn ảnh hưởng lớn tới dữ liệu, kiến trúc, bảo mật hoặc hành vi sản phẩm, dừng phần liên quan và hỏi người dùng.

## 3. Quy trình làm việc trực tiếp

Với mỗi task:

1. Đồng bộ và đọc trạng thái repository, không ghi đè thay đổi chưa rõ nguồn gốc.
2. Tóm tắt ngắn mục tiêu, phạm vi, tiêu chí hoàn thành và rủi ro.
3. Tạo branch riêng từ base branch đã xác minh.
4. Sửa code trực tiếp; không chỉ viết prompt cho công cụ khác.
5. Chạy test, lint, kiểm tra cú pháp, smoke test hoặc render mẫu phù hợp với phạm vi.
6. Kiểm tra `git status`, diff và file phát sinh trước commit.
7. Commit, push branch và tạo/cập nhật PR khi GitHub cho phép.
8. Cập nhật `.ai/CURRENT_CONTEXT.md`, `.ai/TASKS.md` và `.ai/DECISIONS.md` nếu trạng thái hoặc quyết định thay đổi.
9. Báo cho người dùng: đã đổi gì, bằng chứng kỹ thuật, cách chạy app để nghiệm thu, điểm còn thiếu.

## 4. Git và GitHub

- Base branch mặc định: `main`.
- Không push trực tiếp vào `main`; dùng `feat/...`, `fix/...`, `docs/...`, `test/...` hoặc `chore/...`.
- Không force-push, rewrite lịch sử chung hoặc merge PR nếu người dùng chưa yêu cầu rõ.
- Không commit `.env`, token, cookie, credential, dữ liệu riêng tư, `.venv`, cache, log, file tạm hoặc video render nặng nếu task không yêu cầu.
- Mỗi commit phải tập trung vào một thay đổi hợp lý và có message mô tả kết quả.
- PR phải ghi rõ phạm vi, lệnh kiểm tra, kết quả, rủi ro và bước nghiệm thu của người dùng.

## 5. Chất lượng kỹ thuật

Luôn kiểm tra khi có liên quan:

- input SRT không tồn tại, rỗng, sai encoding hoặc sai định dạng;
- đường dẫn có dấu, khoảng trắng và cách chạy trên Windows;
- cấu trúc `annotation.json`, canvas, region, sequence, thời gian và protected regions;
- lỗi thiếu dependency, thiếu font, thiếu codec hoặc không ghi được output;
- tiến trình render dài, retry, hủy, trùng thao tác và file output dang dở;
- tính tương thích Windows trước, sau đó Linux/macOS nếu không làm tăng phạm vi quá mức;
- UI loading, empty, error, disabled, responsive và khả năng thao tác bằng bàn phím khi có giao diện;
- không để nội dung chưa đến lượt bị lộ trong animation;
- không bịa kết quả test hoặc trạng thái GitHub.

## 6. Quy tắc riêng của sản phẩm

- Ngôn ngữ người dùng mặc định là tiếng Việt. Nội dung tiếng Trung từ upstream là dữ liệu cần bản địa hóa, không phải chuẩn giao diện cuối.
- Quy trình sản phẩm phải giữ các cổng xác nhận theo `.ai/PRODUCT_WORKFLOW.md`; Codex không tự render bước sau khi người dùng chưa duyệt bước trước.
- Mỗi cảnh chỉ truyền đạt một ý chính, mặc định 25–35 giây nếu người dùng không chỉ định khác.
- Ảnh nguồn dùng nền giấy vàng kem `#F5EBD7`, nét phác xám đậm, ít màu nhấn; không chứa chữ trong cảnh.
- Animation phải giữ thứ tự kể chuyện từ SRT, che kín vùng chưa vẽ và giữ khung hình hoàn chỉnh ít nhất 0,5 giây cuối cảnh.

## 7. Trạng thái báo cáo

Codex dùng một trong các trạng thái:

- `TECHNICALLY_VERIFIED`: kiểm tra kỹ thuật liên quan đã đạt; chờ hoặc đã có nghiệm thu người dùng.
- `READY_FOR_USER_TEST`: code và kiểm tra tự động đã xong, cần người dùng chạy app.
- `NEEDS_REVISION`: có lỗi hoặc tiêu chí chưa đạt.
- `BLOCKED`: thiếu quyền, dữ liệu, môi trường hoặc quyết định bắt buộc.

Không đồng nhất `TECHNICALLY_VERIFIED` với việc người dùng đã duyệt sản phẩm.
