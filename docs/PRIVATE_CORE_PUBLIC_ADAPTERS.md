# ARIES private-core / public-adapter boundary

This repository is public. Do not place proprietary source, raw derivations, private
training notes, confidential datasets, API keys, or tokens here.

## Recommended separation

- Keep `core_private/`, private training corpora, and unpublished derivations in a
  separate **private local directory or private repository** that is not connected to
  this public repository.
- The public adapter may contain inference interfaces, model configuration, model
  weights that you have rights to release, reproducible evaluation code, and an
  accurate model card.
- A `.gitignore` entry is only a safeguard against accidental future additions. It
  does not remove files already committed, and it does not protect a file if it is
  force-added with `git add -f`.
- Publishing model weights does not reveal the training source code directly, but
  model weights can memorize training data or reveal information. Review the corpus
  and test for memorization before release.
- The experimental frequency-modulation idea is a hypothesis, not a demonstrated
  performance improvement or a proof of a Millennium Prize problem.

## Current status

ARIES's small experimental GPT-2-style model is trained from scratch and can be loaded
with Transformers. The enhanced training wrapper adds a short set of educational
math notes to the base corpus; that small addition is **not evidence** that the model
has learned novel mathematics. The model has not earned an official leaderboard rank.
