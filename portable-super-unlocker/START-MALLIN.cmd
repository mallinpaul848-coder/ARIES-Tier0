@echo off
setlocal
title MALLIN SUPER UNLOCKER
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0MALLIN-Super-Unlocker.ps1"
if errorlevel 1 (
  echo.
  echo The tool stopped with an error. Review the message above.
  pause
)
endlocal
