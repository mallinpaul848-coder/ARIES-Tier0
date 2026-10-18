@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title ARIES AI - One-Click Chat
echo.
echo ARIES AI - One-Click Chat
echo ========================
echo Project folder: %CD%
echo.

if not exist "aries-chat.html" (
  echo ERROR: aries-chat.html was not found.
  echo.
  echo Open the ARIES-Tier0 folder that contains README.md and aries-chat.html.
  pause
  exit /b 1
)

echo Opening the ARIES AI chat in your browser...
echo The chat uses the hosted ARIES API by default.
echo No local Python installation or localhost server is required.
echo.
start "" "%CD%\aries-chat.html"
echo.
echo If the browser opens a blank page, open this file manually:
echo %CD%\aries-chat.html
echo.
echo Hosted API: https://aries-tier0-api-6qjh.onrender.com
echo Keep this window open only if you want to read these instructions.
echo.
pause
endlocal
