@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title ARIES AI - Chat Launcher
echo.
echo ARIES AI - Chat Launcher
echo =======================
echo Project folder: %CD%
echo.

if not exist "aries-chat.html" (
  echo ERROR: aries-chat.html was not found.
  echo Open the extracted ARIES-Tier0-main folder containing README.md.
  pause
  exit /b 1
)

set "PYTHON_EXE="
where python >nul 2>&1 && set "PYTHON_EXE=python"
if not defined PYTHON_EXE (
  where py >nul 2>&1 && set "PYTHON_EXE=py -3"
)
if not defined PYTHON_EXE (
  echo Python 3 is needed to serve the page securely for microphone voice input.
  echo Install it from https://www.python.org/downloads/windows/
  echo During setup, select Add Python to PATH, then run this launcher again.
  echo You can still open aries-chat.html manually, but microphone access may not work.
  start "" "%CD%\aries-chat.html"
  pause
  exit /b 1
)

echo Checking the ARIES chat website...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 'http://127.0.0.1:8081/aries-chat.html'; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
  echo Starting the chat website on localhost port 8081...
  if "%PYTHON_EXE%"=="python" (
    start "ARIES Chat Website - KEEP OPEN" /D "%CD%" cmd.exe /k "python -m http.server 8081 --bind 127.0.0.1"
  ) else (
    start "ARIES Chat Website - KEEP OPEN" /D "%CD%" cmd.exe /k "py -3 -m http.server 8081 --bind 127.0.0.1"
  )
) else (
  echo Chat website is already running.
)

echo Waiting for the chat page...
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8081/aries-chat.html"
echo.
echo ARIES CHAT: http://127.0.0.1:8081/aries-chat.html
echo API: https://aries-tier0-api-6qjh.onrender.com
echo Keep the chat website window open while using ARIES.
echo Voice input uses the microphone button. Spoken replies can be toggled on or off.
echo.
pause
endlocal
