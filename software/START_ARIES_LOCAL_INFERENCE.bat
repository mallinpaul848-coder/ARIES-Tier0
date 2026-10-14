@echo off
setlocal
cd /d "%~dp0.."
title ARIES Tier 0 - Local Inference
echo ==========================================
echo   ARIES Tier 0 - Local Inference Runtime
echo ==========================================
echo.
where llama >nul 2>nul
if errorlevel 1 (
  echo llama.cpp runtime was not found.
  where winget >nul 2>nul
  if errorlevel 1 (
    echo Windows Package Manager winget was not found.
    echo Install llama.cpp from https://github.com/ggml-org/llama.cpp/releases
    echo then reopen this launcher.
    pause
    exit /b 1
  )
  echo Installing the official llama.cpp runtime...
  winget install --id ggml.llamacpp --exact --accept-source-agreements --accept-package-agreements
  if errorlevel 1 (
    echo Automatic installation did not finish. Install llama.cpp from:
    echo https://github.com/ggml-org/llama.cpp/releases
    pause
    exit /b 1
  )
)
where llama >nul 2>nul
if errorlevel 1 (
  echo llama.cpp was installed but the command is not yet on PATH.
  echo Close this window, open a new terminal, then run this launcher again.
  pause
  exit /b 1
)
echo.
echo Starting a local OpenAI-compatible ARIES API.
echo The first run downloads the public Qwen2.5 0.5B GGUF model.
echo Keep this window open. Do not share this local API publicly.
echo API: http://127.0.0.1:8080
echo Health: http://127.0.0.1:8080/health
echo Press Ctrl+C to stop.
echo.
llama serve -hf Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M
pause
