@echo off
setlocal
cd /d "%~dp0.."
title ARIES AI - Self-Hosted Local Engine
echo.
echo  ARIES AI - INDEPENDENT WEBSITE + LOCAL ENGINE
echo  First launch downloads the open model weights (about 1 GB).
echo  Website and chat inference run on this computer.
echo  No hosted AI API or external chat API key is used.
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3 is required. Install from https://www.python.org/downloads/windows/
    pause
    exit /b 1
  )
  set "PY=python"
)
%PY% -c "import llama_cpp, huggingface_hub" >nul 2>nul
if errorlevel 1 (
  echo Installing local model runtime...
  %PY% -m pip install --upgrade pip
  if errorlevel 1 goto failed
  %PY% -m pip install --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu llama-cpp-python huggingface_hub
  if errorlevel 1 goto failed
)
echo.
echo Starting ARIES website at http://127.0.0.1:8081
echo Local inference API: http://127.0.0.1:8765
echo Your browser will open automatically after the model loads.
echo Keep this window open while chatting. Press Ctrl+C to stop.
%PY% software\aries_selfhosted.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Setup failed. Check the error above and ensure the computer has internet access and enough memory.
pause
exit /b 1
