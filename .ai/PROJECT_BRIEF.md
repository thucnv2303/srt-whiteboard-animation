# Project Brief — Tạo video vẽ tay

## Danh tính dự án

- Tên sản phẩm: Tạo video vẽ tay
- Repo làm việc: `thucnv2303/srt-whiteboard-animation`
- Repo upstream: `geeklee/srt-whiteboard-animation`
- Base branch: `main`
- Loại sản phẩm: desktop app Windows + bộ renderer Python local
- Người dùng chính: người làm video tiếng Việt

## Mô hình sản phẩm

ChatGPT Project là studio sáng tạo: nhận ý tưởng ngắn của người dùng rồi chuẩn bị kịch bản, voice, ảnh và metadata cảnh. App desktop là máy dựng: nhận một gói dự án chuẩn, kiểm tra, cho người dùng duyệt và tạo MP4. App không cần AI local và không gọi OpenAI API trong MVP.

## Vấn đề người dùng

Quy trình hiện tại đòi hỏi sao chép nhiều lần giữa kịch bản, ảnh, voice, annotation và lệnh render. Người dùng muốn chỉ đưa ý tưởng, sau đó nhận dự án đồng bộ để app dựng video mà không phải ghép thủ công từng tài nguyên.

## Kết quả sản phẩm

Người dùng có thể:

1. chuẩn bị nội dung trong ChatGPT Project;
2. đưa một folder hoặc ZIP dự án vào app;
3. thấy ngay lỗi thiếu ảnh, annotation hoặc voice;
4. xem danh sách cảnh và chọn nơi xuất;
5. render cảnh, ghép video và gắn voice;
6. xem `final.mp4` rồi phản hồi ý tưởng tiếp theo.

## Phạm vi MVP app

- Desktop app ưu tiên Windows 10/11.
- Input là folder, `project.json` hoặc ZIP theo schema v1.
- Quản lý ảnh cảnh và `annotation.json` cùng basename.
- Voice là tùy chọn; gắn vào video bằng FFmpeg.
- Điều phối renderer upstream, không viết lại thuật toán vẽ.
- UI tiếng Việt có loading, empty, error, disabled, cancel và log.
- Unit test cho hợp đồng dữ liệu và an toàn đường dẫn.

## Milestone sau MVP

- Tự tạo/chỉnh annotation trong app.
- Preview ảnh và timeline đầy đủ.
- Đồng bộ ChatGPT qua plugin/MCP và kho tệp trung gian.
- Đóng gói installer hoặc `.exe`.
- Kiểm tra frame tự động và render regression.

## Ngoài phạm vi hiện tại

- AI local/Ollama.
- OpenAI API gọi từ app.
- Đăng video tự động lên mạng xã hội.
- Hệ thống tài khoản hoặc thanh toán.
- Mobile app native.

## Ràng buộc

- Không commit secret, dữ liệu cá nhân hoặc video render nặng.
- Không tải tài nguyên người dùng lên dịch vụ ngoài nếu chưa được phép.
- Giữ tương thích annotation upstream.
- Người dùng quyết định nghiệm thu sau khi chạy app và xem video.

## Chỉ số thành công MVP

- Người dùng chạy app bằng `run_app.bat` mà không sửa code.
- Gói sai báo lỗi cụ thể, không crash mơ hồ.
- Render chạy ngoài UI thread và không cho thao tác trùng.
- `final.mp4` được tạo đúng thứ tự cảnh; voice được gắn khi có.
- Test/CI có thể chạy lặp lại trước mỗi PR.

