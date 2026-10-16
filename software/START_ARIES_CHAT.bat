@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title ARIES AI - Local Chat Launcher
echo.
echo  ARIES AI - Local Chat Launcher
echo  ==============================
echo  Project folder: %CD%
echo.

where python >nul 2>&1
if not errorlevel 1 (
  set "PY=python"
  goto PYTHON_FOUND
)
where py >nul 2>&1
if not errorlevel 1 (
  set "PY=py -3"
  goto PYTHON_FOUND
)
echo ERROR: Python 3 was not found.
echo Install Python from https://www.python.org/downloads/windows/
echo Enable "Add Python to PATH" during installation if offered.
pause
exit /b 1

:PYTHON_FOUND
echo Python command: %PY%
echo.
echo Starting ARIES local API. Keep the API window open.
start "ARIES Native API - KEEP OPEN" powershell.exe -NoExit -ExecutionPolicy Bypass -File "%CD%\software\run_windows.ps1"

echo Starting local web server. Keep the web server window open.
if "%PY%"=="python" (
  start "ARIES Chat Web Server - KEEP OPEN" cmd.exe /k "python -m http.server 8080 --bind 127.0.0.1"
) else (
  start "ARIES Chat Web Server - KEEP OPEN" cmd.exe /k "py -3 -m http.server 8080 --bind 127.0.0.1"
)

echo.
echo Waiting for local chat page...
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8080/aries-chat.html"
echo.
echo Chat page: http://127.0.0.1:8080/aries-chat.html
echo API health check: http://127.0.0.1:8000/health
echo IMPORTANT: Leave both ARIES windows open while chatting.
echo If the API window says STARTUP FAILED, read the error shown there.
echo.
pause
endlocal
