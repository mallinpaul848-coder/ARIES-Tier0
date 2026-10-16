@echo off
setlocal
cd /d "%~dp0.."
title ARIES AI - Local Chat Launcher

echo.
echo  ARIES AI - Local Chat Launcher
echo  ==============================
echo  Project folder: %CD%
echo.

REM Find a working Python 3 command. Some Windows installs provide "py" instead of "python".
set "PYTHON_CMD=python"
python --version >nul 2>&1
if errorlevel 1 (
    set "PYTHON_CMD=py -3"
    py -3 --version >nul 2>&1
    if errorlevel 1 goto NO_PYTHON
)

echo Python found: %PYTHON_CMD%
echo.
echo Starting the ARIES native API in a separate window...
start "ARIES Native API" powershell -NoExit -ExecutionPolicy Bypass -File "%CD%\software\run_windows.ps1"
echo Starting the local chat page server...
start "ARIES Chat Web Server" cmd /k "%PYTHON_CMD% -m http.server 8080 --bind 127.0.0.1"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8080/aries-chat.html"
echo.
echo Browser: http://127.0.0.1:8080/aries-chat.html
echo Keep both ARIES windows open while chatting.
echo If either window shows an error, leave it open so you can read it.
echo.
pause
endlocal
exit /b 0

:NO_PYTHON
echo ERROR: Python 3 was not found.
echo.
echo Install Python from https://www.python.org/downloads/windows/
echo During installation, enable "Add Python to PATH" if that option appears.
echo Then close this window and double-click START_ARIES_CHAT.bat again.
echo.
pause
exit /b 1
