@echo off
setlocal
cd /d "%~dp0"
title MALLIN Self-Hosted Website
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py --bind 0.0.0.0 --port 8080
  goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
  python server.py --bind 0.0.0.0 --port 8080
  goto :end
)
echo Python 3 is not installed. Install it from https://www.python.org/downloads/windows/
echo Then double-click this file again.
pause
:end
endlocal
