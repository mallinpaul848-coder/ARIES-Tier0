# ARIES experimental causal Transformer

This is an optional research experiment; it does not replace the production ARIES API or its native n-gram baseline.

## What was improved

- Uses causal self-attention so a token cannot attend to future target bytes.
- Trains on real UTF-8 bytes from a user-supplied text file, with next-byte targets shifted by one position.
- Uses gradient clipping, configurable model/training parameters, reproducible training seed, and checkpoint metadata.
- Saves a JSON report containing measured training time and final training loss.
- Keeps PyTorch as an optional dependency rather than adding it to the production API requirements.

This is a small byte-level language-model experiment, not a trillion-token training run. A short corpus and a few hundred steps will not produce a frontier-quality assistant. The code does not establish P = NP or sub-nanosecond generative inference.

## Run on Windows

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-experimental.txt
python experiments\aries_master_model.py --text path\to\your_corpus.txt --steps 500 --checkpoint checkpoints\aries-byte-lm.pt
```

Use a text corpus you have permission to use. Increase steps only after confirming memory use and runtime on your machine. The checkpoint is a research artifact and is not automatically connected to the ARIES chat API.

## Output

The run saves the model checkpoint and a sibling `.report.json`. Training loss is useful for debugging optimization, but it is not an independent evaluation of answer quality. Evaluate on held-out text and task-specific tests before drawing capability conclusions.
