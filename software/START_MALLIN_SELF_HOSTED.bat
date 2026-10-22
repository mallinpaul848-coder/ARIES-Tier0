@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title MALLIN AI - Self-Hosted
echo.
echo MALLIN AI / ARIES TIER ZERO - SELF-HOSTED
echo =========================================
echo This runs on this Windows computer. No Render, Vercel, or hosted API is used.
echo.
where py >nul 2>&1
if errorlevel 1 (
  where python >nul 2>&1
  if errorlevel 1 (
    echo Python 3.11 or newer is required.
    echo Install Python, then run this launcher again.
    pause
    exit /b 1
  )
  set "PY=python"
) else (
  set "PY=py -3"
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating local Python environment...
  %PY% -m venv .venv
  if errorlevel 1 goto fail
)
set "PYTHON=.venv\Scripts\python.exe"
echo Installing the open-source Python packages used by the API...
"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto fail
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto fail
if not exist "models" mkdir models
if not exist "models\aries-native-ngram.json" (
  echo Preparing the built-in ARIES native baseline...
  "%PYTHON%" software\native_runtime.py train --corpus software\deployment_corpus.txt --model models\aries-native-ngram.json
  if errorlevel 1 goto fail
)
set "ARIES_NATIVE_MODEL=%CD%\models\aries-native-ngram.json"
set "ARIES_WEB_ROOT=%CD%\foundation\web"
set "PORT=10000"
echo.
echo Starting the self-hosted MALLIN app.
echo Open http://127.0.0.1:10000/app
echo Keep this window open while using the app.
start "" http://127.0.0.1:10000/app
"%PYTHON%" software\public_native_server.py
goto end
:fail
echo.
echo Setup failed. Read the error above and check your Python installation and internet connection for package installation.
pause
:end
endlocal
