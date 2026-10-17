@echo off
setlocal
cd /d "%~dp0"

where g++ >nul 2>nul
if errorlevel 1 (
  echo ERROR: g++ was not found.
  echo Install a C++ compiler such as MinGW-w64, then reopen this window.
  echo This script does not install software or alter system settings.
  pause
  exit /b 1
)

echo Building ARIES latency benchmark...
g++ -O3 -std=c++17 -Wall -Wextra aries_latency_benchmark.cpp -o aries_latency_benchmark.exe
if errorlevel 1 (
  echo ERROR: Build failed. Review the compiler output above.
  pause
  exit /b 1
)

echo.
echo Running 1,000,000 iterations...
aries_latency_benchmark.exe 1000000
echo.
pause
