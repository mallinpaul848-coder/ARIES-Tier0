# ARIES self-contained local software bootstrap for Windows PowerShell
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
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

Write-Host "1/3 Preparing text corpus..."
python ".\software\data_pipeline.py" --source ".\data\training.txt" --output ".\data\prepared.txt" --report ".\reports\corpus-prep.json"
if ($LASTEXITCODE -ne 0) { throw "Corpus preparation failed." }

Write-Host "2/3 Training local baseline..."
python ".\software\native_runtime.py" train --corpus ".\data\prepared.txt" --model ".\models\aries-native-ngram.json"
if ($LASTEXITCODE -ne 0) { throw "Model training failed." }

Write-Host "3/3 Starting local inference API at http://127.0.0.1:8000"
Write-Host "Keep this window open. In a second PowerShell window, run:"
Write-Host 'python .\tools\aries_bench.py --base-url http://127.0.0.1:8000 --model aries-native --limit 10 --output .\reports\native-benchmark.json'
python ".\software\native_runtime.py" serve --model ".\models\aries-native-ngram.json" --host "127.0.0.1" --port 8000
