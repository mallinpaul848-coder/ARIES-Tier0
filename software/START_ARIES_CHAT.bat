@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title ARIES AI - One-Click Local Chat
echo.
echo  ARIES AI - One-Click Local Chat
echo  =================================
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
echo Enable "Add Python to PATH" if offered, then restart this launcher.
pause
exit /b 1

:PYTHON_FOUND
echo Python command: %PY%
echo.
echo [1/3] Starting ARIES API on port 8000...
start "ARIES API - KEEP OPEN" powershell.exe -NoExit -ExecutionPolicy Bypass -File "%CD%\software\run_windows.ps1"

echo [2/3] Starting chat website on port 8081...
rem Use 8081 for the UI so it cannot collide with the optional llama.cpp API on 8080.
if "%PY%"=="python" (
  start "ARIES Chat Website - KEEP OPEN" cmd.exe /k "python -m http.server 8081 --bind 127.0.0.1"
) else (
  start "ARIES Chat Website - KEEP OPEN" cmd.exe /k "py -3 -m http.server 8081 --bind 127.0.0.1"
)

echo [3/3] Opening the chat page...
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8081/aries-chat.html"

echo.
echo CHAT PAGE: http://127.0.0.1:8081/aries-chat.html
echo API HEALTH: http://127.0.0.1:8000/health
echo.
echo Leave BOTH black windows open while using ARIES.
echo If the API window shows STARTUP FAILED, the API did not start.
echo This launcher uses the built-in small n-gram baseline; it is not a modern LLM.
echo.
pause
endlocal
