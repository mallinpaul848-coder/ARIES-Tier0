@echo off
setlocal
cd /d "%~dp0.."
title ARIES AI - Unified Runtime
echo.
echo ARIES AI - UNIFIED RUNTIME
echo ==========================
echo Starting integrated ARIES API at http://127.0.0.1:8000
echo Keep this window open. Press Ctrl+C to stop.
echo.
set "PY=python"
where python >nul 2>&1
if errorlevel 1 (
  set "PY=py -3"
  where py >nul 2>&1
  if errorlevel 1 (
    echo ERROR: Python 3 was not found. Install Python 3 and select Add Python to PATH.
    pause
    exit /b 1
  )
)
%PY% -c "import fastapi, uvicorn, httpx" >nul 2>&1
if errorlevel 1 (
  echo Installing required ARIES Python packages...
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo ERROR: Could not install requirements.
    pause
    exit /b 1
  )
)
%PY% software\aries_unified.py
if errorlevel 1 (
  echo.
  echo ARIES Unified Runtime stopped with an error.
  pause
)
endlocal
