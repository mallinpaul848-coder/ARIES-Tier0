# ARIES XL Tier Zero — Build and Train

ARIES XL is an approximately 1-billion-parameter target using the repository's existing streaming causal-language-model trainer. This adds configuration and a launcher; it does **not** mean training has completed.

## Configuration

- Width: 1,792
- Transformer blocks: 24
- Attention heads: 14
- Default training sequence length: 1,024 tokens
- Dropout: 0.1
- Seed: 369
- Default tokenizer: offline UTF-8 byte tokenizer
- Approximate parameter target: 1.005 billion; verify against the instantiated model before release
- Default run: 3 optimizer steps for smoke testing
- Full-run target: 1 billion cumulative token exposures, configurable

Byte-token mode does not equal a conventional BPE tokenizer. Report byte-token exposures as such.

## Requirements

Use a supported PyTorch installation and CUDA GPU for practical full training. A 1B-parameter model is not a reasonable full-training workload for a typical free CI runner. FP16 raw weights alone are roughly 2 GB, but training needs additional memory for gradients, optimizer state, activations, and temporary buffers. A 24 GB GPU may support carefully configured experiments; 40–80 GB or multiple GPUs may be needed depending on settings. These are planning guidelines, not measured guarantees.

## Prepare a corpus

Create a UTF-8 text file such as data/aries_corpus.txt using text you own or have permission to use. Keep a separate held-out validation set; remove secrets, personal data, duplicates, and material without training rights. The launcher streams the corpus but does not automatically curate or validate its quality.

## Windows PowerShell

From the repository root, install a PyTorch build compatible with your hardware, then run:

~~~powershell
python -m pip install torch
python training/train_aries_xl.py --corpus data/aries_corpus.txt
~~~

The default is a 3-step smoke run, not full training.

For a full run toward the token-exposure target:

~~~powershell
python training/train_aries_xl.py --corpus data/aries_corpus.txt --full --target-training-tokens 1000000000 --output-dir artifacts/aries-xl-1b
~~~

Use CUDA-enabled PyTorch for practical training. If out of memory, reduce sequence length (for example, to 256 or 512), keep batch size at 1, and consider gradient checkpointing or optimizer sharding. The current underlying trainer does not automatically enable all memory-saving techniques.

Resume from a saved checkpoint:

~~~powershell
python training/train_aries_xl.py --corpus data/aries_corpus.txt --full --resume-from-checkpoint latest --output-dir artifacts/aries-xl-1b
~~~

## Release validation

1. Record GPU model, VRAM, driver, PyTorch/CUDA versions, corpus hash, tokenizer mode, and command.
2. Confirm actual parameter count from the instantiated model.
3. Record training loss and held-out validation loss/perplexity.
4. Evaluate on a fixed prompt set; report failures as well as successes.
5. Measure time-to-first-token, tokens/second, peak VRAM, and checkpoint size on named hardware.
6. Compare baseline and ARIES XL on identical hardware, prompts, decoding settings, and data splits.
7. Verify checkpoint loading in a clean environment before publishing.

A token-exposure target is not proof of completion, unique-token count, or quality. The custom architecture is not automatically compatible with standard Hugging Face model loading. This source change does not provide trained weights, prove improved reasoning, solve P=NP, or establish a leaderboard score.
