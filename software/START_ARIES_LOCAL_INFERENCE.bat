@echo off
setlocal
cd /d "%~dp0.."
title ARIES Local Inference Setup
echo ==========================================
echo   ARIES Tier 0 - Local Inference Runtime
echo ==========================================
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11 or 3.12 from https://www.python.org/downloads/windows/
  echo During setup, check "Add Python to PATH".
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating isolated Python environment...
  py -3.12 -m venv .venv 2>nul
  if errorlevel 1 py -3.11 -m venv .venv
  if errorlevel 1 (
    echo Could not create virtual environment. Install Python 3.11 or 3.12.
    pause
    exit /b 1
  )
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r software\requirements-inference.txt
if errorlevel 1 (
  echo.
  echo Inference dependency installation failed. This can happen if a compatible wheel
  echo is unavailable for your Python/Windows version. See software\LOCAL_INFERENCE.md.
  pause
  exit /b 1
)
python software\download_model.py
if errorlevel 1 (
  pause
  exit /b 1
)
echo.
echo Starting ARIES. Keep this window open.
echo API: http://127.0.0.1:8080
echo Health: http://127.0.0.1:8080/health
echo Press Ctrl+C to stop.
python software\aries_inference_server.py
pause
