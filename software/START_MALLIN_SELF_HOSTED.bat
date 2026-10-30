@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title MALLIN AI - Self-Hosted
echo.
echo MALLIN AI / ARIES TIER ZERO - SELF-HOSTED
echo =========================================
echo This runs on this Windows computer. No Render, Vercel, Cloudflare, or hosted AI API is used.
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
if not exist "models\aries-model.gguf" (
  echo.
  echo OPTIONAL: install a small local language model for general question answering?
  echo This downloads an approximately 0.5B-parameter public GGUF model.
  echo It is not ARIES-trained weights. The model runs on this computer and prompts stay local.
  choice /C YN /N /M "Download and install local model? [Y/N] "
  if errorlevel 2 goto no_model
  echo Installing the local CPU inference runtime...
  "%PYTHON%" -m pip install -r software\requirements-inference.txt
  if errorlevel 1 (
    echo.
    echo The local inference runtime could not be installed on this Python/Windows setup.
    echo ARIES will still start in native-baseline mode. No external AI API will be used.
    goto no_model
  )
  echo Downloading the public GGUF model...
  set "ARIES_GGUF_MODEL_PATH=%CD%\models\aries-model.gguf"
  "%PYTHON%" software\download_model.py
  if errorlevel 1 (
    echo Model download failed. ARIES will start in native-baseline mode.
    goto no_model
  )
)
:no_model
set "ARIES_NATIVE_MODEL=%CD%\models\aries-native-ngram.json"
set "ARIES_GGUF_MODEL_PATH=%CD%\models\aries-model.gguf"
set "ARIES_INDEPENDENT_MODE=1"
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
