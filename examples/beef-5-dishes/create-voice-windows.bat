@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0create-voice-windows.ps1"
if errorlevel 1 (
  echo Khong tao duoc voice. Hay chup lai loi va gui cho Codex.
  pause
  exit /b 1
)
pause

