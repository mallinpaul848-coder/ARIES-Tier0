@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title ARIES Tier 0 - Windows Startup Diagnostics
echo.
echo ==========================================
echo   ARIES Tier 0 - Startup Diagnostics
echo ==========================================
echo Project folder: %CD%
echo Log file: %CD%\aries-startup-diagnostics.txt
echo.

(
  echo ARIES Windows startup diagnostics
  echo Date: %DATE% %TIME%
  echo Project folder: %CD%
  echo.
  echo --- Python commands ---
  where python
  python --version
  echo.
  where py
  py -3 --version
  echo.
  echo --- Required files ---
  if exist "software\run_windows.ps1" (echo OK: software\run_windows.ps1) else (echo MISSING: software\run_windows.ps1)
  if exist "software\native_runtime.py" (echo OK: software\native_runtime.py) else (echo MISSING: software\native_runtime.py)
  if exist "aries-chat.html" (echo OK: aries-chat.html) else (echo MISSING: aries-chat.html)
  echo.
  echo --- Port 8000 ---
  netstat -ano ^| findstr ":8000"
  echo.
  echo --- Port 8080 ---
  netstat -ano ^| findstr ":8080"
) > "aries-startup-diagnostics.txt" 2>&1

type "aries-startup-diagnostics.txt"
echo.
echo Diagnostics saved to:
echo %CD%\aries-startup-diagnostics.txt
echo.
echo This window will stay open. Take a photo or copy the error text
echo and send it in ChatGPT so the exact startup failure can be fixed.
echo.
pause
endlocal
