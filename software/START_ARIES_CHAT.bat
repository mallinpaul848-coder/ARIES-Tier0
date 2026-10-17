@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title ARIES AI - One-Click Local Chat
echo.
echo ARIES AI - One-Click Local Chat
echo =================================
echo Project folder: %CD%
echo.

if not exist "aries-chat.html" (
  echo ERROR: aries-chat.html is missing.
  echo You may have opened the wrong ARIES-Tier0-main folder.
  echo Open the folder that contains README.md, aries-chat.html, and software.
  pause
  exit /b 1
)
if not exist "software\run_windows.ps1" (
  echo ERROR: software\run_windows.ps1 is missing.
  pause
  exit /b 1
)

set "PYTHON_EXE="
where python >nul 2>&1 && set "PYTHON_EXE=python"
if not defined PYTHON_EXE (
  where py >nul 2>&1 && set "PYTHON_EXE=py -3"
)
if not defined PYTHON_EXE (
  echo ERROR: Python 3 was not found.
  echo Install Python from https://www.python.org/downloads/windows/
  echo During installation, check "Add Python to PATH".
  pause
  exit /b 1
)

echo Python command found: %PYTHON_EXE%
echo.
echo Checking whether the chat website is already running...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 'http://127.0.0.1:8081/aries-chat.html'; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
  echo Starting chat website on port 8081...
  if "%PYTHON_EXE%"=="python" (
    start "ARIES Chat Website - KEEP OPEN" /D "%CD%" cmd.exe /k "python -m http.server 8081 --bind 127.0.0.1"
  ) else (
    start "ARIES Chat Website - KEEP OPEN" /D "%CD%" cmd.exe /k "py -3 -m http.server 8081 --bind 127.0.0.1"
  )
) else (
  echo Chat website is already running.
)

echo.
echo Checking whether the local API is already running...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 'http://127.0.0.1:8000/health'; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
  echo Starting ARIES API on port 8000...
  start "ARIES API - KEEP OPEN" /D "%CD%" powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -File "%CD%\software\run_windows.ps1"
) else (
  echo ARIES API is already running.
)

echo.
echo Waiting for the chat page...
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8081/aries-chat.html"
echo.
echo CHAT PAGE: http://127.0.0.1:8081/aries-chat.html
echo LOCAL API HEALTH: http://127.0.0.1:8000/health
echo.
echo Leave the ARIES API and chat website windows open.
echo If the API does not start, its window will show the error.
echo Note: the built-in model is a small baseline, not a trillion-token-trained LLM.
echo.
pause
endlocal
