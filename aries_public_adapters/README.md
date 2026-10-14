# ARIES public evaluation adapter boundary

This directory is for public, reviewable interfaces and evaluation metadata only. Do not place proprietary source, raw derivations, private datasets, tokens, or unpublished proofs here.

## Allowed contents

- API/request/response adapters and benchmark invocation scripts
- Public model cards, evaluation metadata, and reproducibility instructions
- Reviewed configuration/tokenizer files and model artifacts only after licensing, provenance, and memorization review

## Not allowed

- `core_private/` source or private derivation files
- Raw private training corpora or unpublished proof material
- API keys, Hugging Face tokens, private keys, or credentials
- A claim that a model is leaderboard-eligible or ranked without official confirmation

## Release checklist

1. Review the exact staged file list and Git diff before publishing.
2. Verify training-data provenance, licensing, and attribution.
3. Check model outputs for memorization or leakage of sensitive training content.
4. Run the model loader smoke test against the exact exported artifact.
5. Publish a model card describing architecture, training data, limitations, and measured evaluations.
6. Keep the proprietary source in a separate private repository or local directory. `.gitignore` alone is not a security boundary.
7. Record official leaderboard submission and results only after receiving actual confirmation.

The ARIES experimental frequency-modulation layer is a hypothesis unless supported by controlled comparative measurements. Do not imply that a 3-6-9-inspired mechanism improves performance without baseline comparisons and reproducible results.
