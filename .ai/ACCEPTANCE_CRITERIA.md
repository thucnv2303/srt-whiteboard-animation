# Tiêu chí chấp nhận

## Cho mọi task code

- [ ] Hành vi mới khớp yêu cầu mới nhất của người dùng.
- [ ] Không có thay đổi ngoài phạm vi hoặc file sinh ra ngoài ý muốn.
- [ ] Input lỗi có thông báo rõ và không làm hỏng dữ liệu hiện có.
- [ ] Không commit secret, `.venv`, cache, log hoặc output nặng ngoài yêu cầu.
- [ ] Test/check liên quan đã chạy với output thật.
- [ ] Branch, commit SHA và PR được cung cấp khi GitHub cho phép.
- [ ] `.ai/CURRENT_CONTEXT.md` và `.ai/TASKS.md` được cập nhật nếu trạng thái đổi.
- [ ] Có bước rõ ràng để người dùng chạy app nghiệm thu.

## SRT và chia cảnh

- [ ] Đọc được UTF-8 và UTF-8 BOM.
- [ ] Timestamp dùng dấu phẩy hoặc dấu chấm được xử lý.
- [ ] File không tồn tại, không có cue hoặc cue lỗi trả lỗi dễ hiểu.
- [ ] Cue giữ đúng thứ tự và duration không âm.
- [ ] Scene không vượt `max-sec` ngoài trường hợp được mô tả rõ.

## Annotation và preview

- [ ] PNG và annotation dùng cùng basename.
- [ ] Canvas khớp kích thước ảnh.
- [ ] Region là số nguyên, kích thước dương và nằm trong canvas.
- [ ] Sequence liên tục từ 1 và khớp mạch subtitle.
- [ ] Start/duration hợp lệ, vùng mặc định không vẽ chồng thời gian.
- [ ] Loading/empty/error/disabled states không gây thao tác trùng.
- [ ] Lưu file có cảnh báo ghi đè hoặc cơ chế an toàn phù hợp.

## Render

- [ ] First frame không lộ nét vẽ ngoài nền giấy.
- [ ] Vùng chưa đến lượt và protected regions không bị lộ ở mid-frame.
- [ ] Tay/bút bám hợp lý vào nét đang vẽ.
- [ ] Final frame hiển thị ảnh đầy đủ ít nhất 500 ms.
- [ ] Output MP4 tồn tại, đọc được và có thời lượng hợp lý.
- [ ] Khi ghép, thứ tự cảnh và kích thước/codec được xử lý đúng hoặc báo lỗi rõ.

## Nghiệm thu người dùng

- [ ] Người dùng chạy app theo hướng dẫn trên môi trường thật.
- [ ] Người dùng xác nhận luồng thao tác dễ hiểu.
- [ ] Người dùng xác nhận hình/video đúng ý tưởng hoặc ghi rõ điểm cần sửa.

Chỉ đánh dấu phần nghiệm thu người dùng sau khi nhận phản hồi thực tế; không suy đoán từ test tự động.
