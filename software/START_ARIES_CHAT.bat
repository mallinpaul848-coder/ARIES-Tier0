@echo off
setlocal
cd /d "%~dp0.."
echo.
echo  ARIES AI - Local Chat Launcher
echo  ==============================
echo.
echo Starting the ARIES native API in a separate window...
start "ARIES Native API" powershell -NoExit -ExecutionPolicy Bypass -File "%CD%\software\run_windows.ps1"
echo Starting the local chat page server...
start "ARIES Chat Web Server" cmd /k python -m http.server 8080 --bind 127.0.0.1
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8080/aries-chat.html"
echo.
echo Browser: http://127.0.0.1:8080/aries-chat.html
echo Keep both ARIES windows open while chatting.
echo Close their windows to stop the services.
endlocal
