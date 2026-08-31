@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Dang chuan bi moi truong lan dau...
  python scripts\prepare_env.py
  if errorlevel 1 (
    echo Khong the chuan bi moi truong. Hay chup lai man hinh loi va gui cho Codex.
    pause
    exit /b 1
  )
)

".venv\Scripts\python.exe" -m whiteboard_app
if errorlevel 1 (
  echo App da dung do co loi. Hay chup lai man hinh nay va gui cho Codex.
  pause
  exit /b 1
)

