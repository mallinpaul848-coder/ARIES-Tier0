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
- Training steps: 1000
- Random seed: 369
- Corpus file name: training.txt (the corpus itself is not uploaded by this script)
- Declared corpus provenance: Salesforce/wikitext wikitext-2-raw-v1 fallback; see dataset card and license. If a custom corpus path is supplied, uploader is responsible for its provenance and rights.

## Intended use and limitations

This is an experimental baseline. No claim is made that it matches modern foundation models, is leaderboard-eligible, or has strong general-purpose performance. Evaluate independently before use. Small or narrow training corpora can cause memorization, poor coverage, and inaccurate outputs.

## Training data and rights

Declared provenance: Salesforce/wikitext wikitext-2-raw-v1 fallback; see dataset card and license. If a custom corpus path is supplied, uploader is responsible for its provenance and rights.

The uploader is responsible for checking the dataset card, license, attribution, and whether the corpus and resulting model may lawfully be used and redistributed. Do not publish an inaccurate license claim.

## Evaluation

No independent benchmark score is claimed. Run reproducible evaluation on a pinned revision before reporting performance.
