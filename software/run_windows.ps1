# ARIES self-contained local software bootstrap for Windows PowerShell
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Support both common Windows Python entry points: "python" and "py -3".
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    $script:AriesPython = $pythonCommand.Source
    $script:AriesPythonPrefix = @()
} else {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        Write-Host ""
        Write-Host "ERROR: Python 3 was not found. Install it from https://www.python.org/downloads/windows/" -ForegroundColor Red
        Write-Host "If offered, select 'Add Python to PATH', then reopen this launcher."
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
    New-Item -ItemType Directory -Force data, models, reports | Out-Null

    if (-not (Test-Path ".\data\training.txt")) {
@'
ARIES is an experimental local-first language system.
A reliable system measures actual outputs and reports uncertainty honestly.
A freight dispatcher compares pickup location, destination, equipment, dates, deadhead miles, rate, and broker reliability.
A safe dispatch process confirms cargo details, pickup instructions, delivery requirements, insurance, and payment terms.
A benchmark records prompts, responses, latency, and scoring rules so results can be reproduced.
'@ | Set-Content -Encoding utf8 ".\data\training.txt"
        Write-Host "Created a tiny sample corpus. Replace it with legally obtained training text for real experiments."
    }

    Write-Host "Python command: $($script:AriesPython) $($script:AriesPythonPrefix -join ' ')"
    Write-Host "1/3 Preparing text corpus..."
    Invoke-AriesPython ".\software\data_pipeline.py" --source ".\data\training.txt" --output ".\data\prepared.txt" --report ".\reports\corpus-prep.json"

    Write-Host "2/3 Training local baseline..."
    Invoke-AriesPython ".\software\native_runtime.py" train --corpus ".\data\prepared.txt" --model ".\models\aries-native-ngram.json"

    Write-Host "3/3 Starting local inference API at http://127.0.0.1:8000"
    Write-Host "Keep this window open while chatting. To stop the API, press Ctrl+C."
    Invoke-AriesPython ".\software\native_runtime.py" serve --model ".\models\aries-native-ngram.json" --host "127.0.0.1" --port 8000
    if ($LASTEXITCODE -ne 0) { throw "The ARIES API server stopped with exit code $LASTEXITCODE." }
} catch {
    Write-Host ""
    Write-Host "ARIES STARTUP FAILED:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Read the error above. Check that Python 3 is installed and that port 8000 is not already in use."
    Read-Host "Press Enter to close this window"
    exit 1
}
