# ARIES Native Runtime (standalone baseline)

This adds a genuinely local inference path implemented with Python's standard library. It does not import FastAPI, PyTorch, Transformers, Lighteval, Hugging Face, or call an upstream model API.

**Honest limitation:** the included runtime is a character-level n-gram model, not a competitive foundation LLM. It must be trained on text you supply. It demonstrates standalone model training, local model-file loading, text generation, and an OpenAI-compatible HTTP endpoint. Do not represent it as equivalent to a modern LLM or claim benchmark scores without measuring them.

## Windows quick start

From the repository root in PowerShell:

```powershell
New-Item -ItemType Directory -Force data | Out-Null
@'
ARIES is a local-first experimental language system.
A model learns patterns from the training examples provided to it.
A dispatcher compares pickup, destination, timing, equipment, and costs.
A careful assistant explains uncertainty and does not invent measurements.
The purpose of this sample text is to demonstrate local training and inference.
'@ | Set-Content -Encoding utf8 data/training.txt

python .\software\native_runtime.py train --corpus .\data\training.txt --model .\aries-native-ngram.json
python .\software\native_runtime.py serve --model .\aries-native-ngram.json --host 127.0.0.1 --port 8000
```

Keep the server terminal open. In a second PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$body = @{
  model = "aries-native"
  messages = @(@{ role = "user"; content = "ARIES is" })
  max_tokens = 120
  temperature = 0.7
} | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/v1/chat/completions -Method Post -ContentType "application/json" -Body $body
```

Use a substantially larger, legally obtained, clean text corpus for meaningful experiments. The sample corpus only verifies the training and serving pipeline.

## Components

- `native_runtime.py`: trainer, model-file loader, text generation, HTTP API.
- `aries_bench.py`: separate dependency-free endpoint diagnostic suite.
- Model weights are generated locally as a JSON file and should not be committed if large or sensitive.

## Running the benchmark against this native server

In another PowerShell window, from the repository root:

```powershell
python .\tools\aries_bench.py --base-url http://127.0.0.1:8000 --model aries-native --limit 10
```

The tiny n-gram model will likely score poorly on exact-answer tasks; that is an honest baseline, not a bug in the evaluator. The existing Render FastAPI service remains a separate upstream-proxy deployment unless its architecture is explicitly changed. This native runtime runs on the operator's own machine and is not automatically deployed to Render.
