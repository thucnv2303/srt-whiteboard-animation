# 5 món ăn từ thịt bò tốt cho bé

Dự án mẫu khoảng 50 giây gồm ảnh món ăn bán chân thực, năm vùng vẽ, kịch bản/phụ đề tiếng Việt và nhãn bút `Ăn dặm mẹ Dâu`.

## Tạo voice Việt neural

Nhấp đúp `create-voice-neural.bat`. Lần đầu script tự cài `edge-tts`, sau đó dùng giọng nữ `vi-VN-HoaiMyNeural` để tạo `voice.mp3` từ `script.txt`.

Cách này không cần API key và không bị lỗi đọc tiếng Việt như voice SAPI mặc định, nhưng máy cần có Internet lúc tạo voice. Sau khi thấy dòng `Đã tạo xong voice.mp3`, mở app và chọn `project.json` trong cùng thư mục.

## Tùy chỉnh

- Sửa `script.txt`, chạy lại batch để tạo voice mới.
- Đổi `penBrand` trong `project.json` để đổi chữ đi theo cây bút (tối đa 40 ký tự).
- Có thể thay `voice.mp3` bằng voice do ChatGPT Project xuất ra, miễn giữ nguyên tên file hoặc cập nhật trường `voice`.
- Hai script `create-voice-windows.*` cũ chỉ được giữ làm phương án offline; chất lượng tiếng Việt phụ thuộc voice đã cài trong Windows.
