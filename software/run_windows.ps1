# ARIES Unified Runtime launcher for Windows PowerShell
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    & $pythonCommand.Source --version *> $null
    if ($LASTEXITCODE -ne 0) { $pythonCommand = $null }
}
if ($pythonCommand) {
    $script:AriesPython = $pythonCommand.Source
    $script:AriesPythonPrefix = @()
} else {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        & $pythonCommand.Source -3 --version *> $null
        if ($LASTEXITCODE -ne 0) { $pythonCommand = $null }
    }
    if (-not $pythonCommand) {
        Write-Host ""
        Write-Host "ERROR: Python 3 was not found. Install it from https://www.python.org/downloads/windows/" -ForegroundColor Red
        Write-Host "Select 'Add Python to PATH' during installation, then reopen ARIES."
        Read-Host "Press Enter to close"
        exit 1
    }
    $script:AriesPython = $pythonCommand.Source
    $script:AriesPythonPrefix = @("-3")
}

function Invoke-AriesPython {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$PythonArgs)
    & $script:AriesPython @script:AriesPythonPrefix @PythonArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed (exit code $LASTEXITCODE): $($PythonArgs -join ' ')"
    }
}

try {
    Write-Host ""
    Write-Host "ARIES AI - UNIFIED RUNTIME 9.0.0"
    Write-Host "Python: $($script:AriesPython) $($script:AriesPythonPrefix -join ' ')"
    Write-Host "Checking required packages..."
    & $script:AriesPython @script:AriesPythonPrefix -c "import fastapi, uvicorn, httpx" *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing ARIES dependencies from requirements.txt..."
        Invoke-AriesPython -m pip install -r ".\requirements.txt"
    }
    Write-Host ""
    Write-Host "Starting unified ARIES API at http://127.0.0.1:8000"
    Write-Host "Health: http://127.0.0.1:8000/health"
    Write-Host "Chat API: http://127.0.0.1:8000/v1/chat/completions"
    Write-Host "Performance metrics: http://127.0.0.1:8000/performance"
    Write-Host "Keep this window open. Press Ctrl+C to stop the API."
    Invoke-AriesPython ".\software\aries_unified.py"
} catch {
    Write-Host ""
    Write-Host "ARIES UNIFIED STARTUP FAILED:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Check that port 8000 is free and the dependencies installed correctly."
    Read-Host "Press Enter to close this window"
    exit 1
}
