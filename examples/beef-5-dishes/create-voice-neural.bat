@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0\..\.."

echo Đang kiểm tra môi trường và giọng đọc...
python scripts\prepare_env.py
if errorlevel 1 (
  echo Không thể cài edge-tts. Hãy kiểm tra kết nối Internet rồi thử lại.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" "examples\beef-5-dishes\create_voice_neural.py"
if errorlevel 1 (
  echo Tạo voice thất bại. Hãy chụp cửa sổ này và gửi cho Codex.
  pause
  exit /b 1
)

echo.
echo Đã tạo xong voice.mp3. Bây giờ có thể mở project.json trong app.
pause
