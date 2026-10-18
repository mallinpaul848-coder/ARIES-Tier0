# ARIES Master Model research prototype

This folder contains an **experimental** PyTorch decoder-only Transformer inspired by the user-supplied ARIES master-engine draft.

## What is integrated

- Token and learned positional embeddings.
- Optional, bounded 3/6/9-inspired feature gate (near unity to avoid activation blow-up).
- Causal multi-head self-attention, pre-normalization, GELU feed-forward layers, residual paths, and tied token/output weights.
- Next-token cross-entropy loss, greedy or temperature-based sampling, top-k filtering, and parameter counting.
- Tests for tensor shapes, finite loss, causal masking, generation, and invalid context lengths.

## Run tests

From repository root after installing a compatible PyTorch build:

```powershell
python -m unittest tests.test_aries_master_model -v
```

Minimal smoke example:

```python
import torch
from aries_math.aries_master_model import AriesMasterModel, count_parameters

model = AriesMasterModel(vocab_size=128, d_model=64, n_layers=2, n_heads=4, max_seq_len=128)
tokens = torch.randint(0, 128, (2, 16))
result = model(tokens, labels=tokens)
print("parameters:", count_parameters(model))
print("training loss:", float(result["loss"]))
```

## Important boundaries

This is a randomly initialized prototype. It is **not connected to the production HTTP chat endpoint**, whose currently documented backend is the native character n-gram baseline. The prototype needs a tokenizer, a curated/licensed training corpus, a training loop, checkpointing, compute, and quality evaluation before it can replace that backend.

A data generator that emits random token IDs is not language training. No trillion-token training is started by this module. No claim is made that 3/6/9 features solve P vs NP, that the model is smarter than established models, or that inference is sub-nanosecond. Benchmark quality and latency on actual hardware and publish reproducible test settings.
