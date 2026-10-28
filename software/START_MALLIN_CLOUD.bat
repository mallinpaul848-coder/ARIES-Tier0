@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title MALLIN Cloud - Self-Hosted
echo.
echo MALLIN CLOUD - YOUR OWN WINDOWS SERVER
echo ======================================
echo No Render, Vercel, Pages host, or external AI API is required.
echo This PC must stay on for the service to remain available.
echo.
where py >nul 2>&1
if errorlevel 1 (
  where python >nul 2>&1
  if errorlevel 1 (
    echo Python 3.11 or newer is required.
    pause
    exit /b 1
  )
  set "PY=python"
) else (
  set "PY=py -3"
)
where git >nul 2>&1
if errorlevel 1 (
  echo Git for Windows is required for repository deployments.
  echo You can install Git later; the dashboard itself can still be tested without it.
  pause
)
if not exist ".venv-mallin-cloud\Scripts\python.exe" (
  echo Creating private Python environment...
  %PY% -m venv .venv-mallin-cloud
  if errorlevel 1 goto fail
)
set "PYTHON=.venv-mallin-cloud\Scripts\python.exe"
echo Installing MALLIN Cloud Python packages...
"%PYTHON%" -m pip install -r mallin-cloud\requirements.txt
if errorlevel 1 goto fail
if not exist "mallin-cloud-data" mkdir "mallin-cloud-data"
set "MALLIN_DATA_DIR=%CD%\mallin-cloud-data"
if "%MALLIN_ADMIN_TOKEN%"=="" (
  echo.
  echo Set a private admin token for deployment control.
  set /p MALLIN_ADMIN_TOKEN=Admin token (make it long and unique): 
)
if "%MALLIN_ADMIN_TOKEN%"=="" (
  echo An admin token is required; refusing to start deployment controls without it.
  pause
  exit /b 1
)
set "PORT=8787"
echo.
echo Starting your local MALLIN Cloud server...
echo Dashboard: http://127.0.0.1:8787
echo Health:    http://127.0.0.1:8787/health
echo Keep this window open. Do not port-forward this development server to the public internet.
start "" http://127.0.0.1:8787
"%PYTHON%" -m uvicorn app:app --app-dir mallin-cloud --host 127.0.0.1 --port 8787
goto end
:fail
echo.
echo Startup failed. Check the error above, Python, and your internet connection.
pause
:end
endlocal
