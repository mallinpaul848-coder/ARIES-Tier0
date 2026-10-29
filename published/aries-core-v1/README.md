---
license: other
language:
- en
library_name: transformers
pipeline_tag: text-generation
tags:
- aries
- causal-lm
- trained-from-scratch
---

# ARIES Experimental Causal LM

## Summary

An experimental, small GPT-2-style causal language model trained from randomly initialized weights on a user-supplied text corpus. This is not the ARIES hosted API proxy and is not a conversion of the existing character n-gram baseline.

## Model details

- Architecture: GPT-2 causal language model (GPT2LMHeadModel)
- Parameters: 5,273,088
- Layers / hidden size / attention heads: 4 / 256 / 4
- Context length: 256 tokens
- Tokenizer vocabulary: 8000
- Training steps: 100000
- Random seed: 369
- Corpus file name: training_with_math_curriculum.txt (the corpus itself is not uploaded by this script)
- Declared corpus provenance: Base corpus: data/training.txt (10,916,753 characters; verify its license and attribution). Supplement: 7 short ARIES-authored educational math notes. These notes are training examples, not proofs of Millennium Prize problems.

## Intended use and limitations

This is an experimental baseline. No claim is made that it matches modern foundation models, is leaderboard-eligible, or has strong general-purpose performance. Evaluate independently before use. Small or narrow training corpora can cause memorization, poor coverage, and inaccurate outputs.

## Training data and rights

Declared provenance: Base corpus: data/training.txt (10,916,753 characters; verify its license and attribution). Supplement: 7 short ARIES-authored educational math notes. These notes are training examples, not proofs of Millennium Prize problems.

The uploader is responsible for checking the dataset card, license, attribution, and whether the corpus and resulting model may lawfully be used and redistributed. Do not publish an inaccurate license claim.

## Evaluation

No independent benchmark score is claimed. Run reproducible evaluation on a pinned revision before reporting performance.


## Publication status and evidence boundary

The checkpoint is prepared for private Hugging Face publication and smoke verification by the repository workflow `.github/workflows/publish-aries-private.yml`. This workflow uploads to `paulmallin777/aries-core-v1` as a private repository, checks that the required model and tokenizer files exist, and runs a short local generation smoke test before upload. It does not publish the model publicly, certify model quality, establish leaderboard eligibility, or claim independent evaluation. Public release remains gated on reviewing the training corpus license, attribution, and redistribution rights.
