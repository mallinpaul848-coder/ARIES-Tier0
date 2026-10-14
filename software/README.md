# ARIES independent software modules

This directory is the local-first software path, separate from the hosted Render API proxy.

- `native_runtime.py` — local training, model-file loading, generation, HTTP API.
- `data_pipeline.py` — text normalization, duplicate removal, corpus manifest and SHA-256 hashes.
- `evaluate_native.py` — held-out character-level negative log-likelihood/perplexity.
- `run_windows.ps1` — creates a sample corpus if needed, prepares data, trains a baseline and starts local API.
- `NATIVE_RUNTIME.md` — manual setup and API examples.

## One-command Windows start

From a PowerShell window after cloning the repository:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\software\run_windows.ps1
```

The first run creates a small demonstration corpus. Replace `data/training.txt` with a larger, legally obtained corpus before serious experiments. Run the benchmark in a second terminal while the server is running.

This code is independent of external model APIs and third-party inference frameworks, but the included model is only a small character n-gram baseline. A strong LLM needs a capable architecture, large training corpus, compute, and trained weights. This software does not conjure those assets automatically and is not yet a substitute for a modern LLM.
