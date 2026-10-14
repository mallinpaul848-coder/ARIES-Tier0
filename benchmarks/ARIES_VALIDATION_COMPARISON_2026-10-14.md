# ARIES Tier 0 — External Validation and Model Comparison

**Report date:** 2026-10-14  
**Repository revision for latest public validation:** `23559113c32bb75e04bc09379d276b70d4feb2dd`  
**Scope:** software tests, API deployment checks, microbenchmark, model packaging readiness, and comparison against a public third-party evaluation index.

## Executive result

| Area | Result | Meaning |
|---|---|---|
| ARIES fast-path tests | **16/16 passed** | Cache behavior, cache bounds, timer metadata, and rule-engine regression tests passed on GitHub Actions run [38617112178](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38617112178). These tests ran on the same software revision; the later revision changed the public endpoint validation workflow. |
| Current public endpoint | **Passed** | The public check ran on revision `2355911`, including the new `GET /performance` checks and a successful ten-case request set: [run 38617276795](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38617276795). |
| Ten-case public diagnostic | **10/10 exact matches** | Mean 131.491 ms; median 117.229 ms; minimum 106.122 ms; maximum 212.399 ms as seen from a GitHub-hosted runner. These are authored, narrow task checks and not an independent general-capability benchmark. |
| API tests / end-to-end API / RTL smoke tests | **Passed on revision 2355911** | See [API tests](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38617276799), [end-to-end integration](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38617276969), and [RTL smoke test](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38617276783). |
| Official model leaderboard | **Not submitted** | No official queue entry or rank is verified. Public API checks are not an official leaderboard submission. |

## Measured local microbenchmark

The latency workflow ran 20,000 timed iterations per case on a GitHub-hosted Linux runner (Python 3.12.15, x86_64, 4 logical CPUs; the reported monotonic timer resolution was 1 ns).

| Operation | Mean elapsed time per call | Calls/second |
|---|---:|---:|
| Direct deterministic reasoner, no memoization | 4,936.06 ns (4.94 µs) | 202,591 |
| Fast-path wrapper, cache disabled | 7,091.13 ns (7.09 µs) | 141,021 |
| Fast-path unique prompt/cache miss | 7,684.15 ns (7.68 µs) | 130,138 |
| Fast-path repeated prompt/cache hit | 1,692.61 ns (1.69 µs) | 590,802 |

Machine-readable evidence: [workflow run 38617112178](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38617112178) and [artifact 11919372898](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38617112178/artifacts/11919372898).

**Interpretation:** the cache-hit measurement is a repeated deterministic response lookup plus Python overhead, not generated text inference. Nanosecond units do not imply sub-nanosecond latency. The report records `sub_nanosecond_latency_verified: false`. The public endpoint's network-visible time is measured in milliseconds and includes network/hosting/runtime overhead.

## Keep the two ARIES models distinct

### Deployed public API

The API reports model ID `aries-native-ngram`, uses an ARIES-owned character n-gram baseline trained on a short corpus (the latest recorded diagnostic showed 2,164 trained characters), and has a deterministic task engine for a limited set of tasks. Its 10/10 score reflects exactly those authored test cases, which overlap with the rule engine's supported functions. It does not establish broad language-model competence.

### Experimental Transformer checkpoint

The public GitHub path [`published/aries-core-v1`](https://github.com/mallinpaul848-coder/ARIES-Tier0/tree/main/published/aries-core-v1) includes `model.safetensors`, `config.json`, `tokenizer.json`, and `tokenizer_config.json`. Its model card describes a small GPT-2-style model trained from randomly initialized weights, with 5,273,088 parameters, 4 layers, 256 hidden dimensions, 4 attention heads, 256-token context, 8,000-token vocabulary, and 1,000 training steps. A prior GitHub workflow reported 141.0151 seconds of training and final training loss 6.508822. Those are packaging/training facts, not evidence of competitive language-model quality.

The model card also says the training corpus has declared provenance that still requires a license/attribution check. Confirm redistribution and training-data rights before publishing weights to another hub.

## Comparison with a current leading model

Artificial Analysis currently lists **Claude Opus 5.5 (Max, Default Fallback)** at **58** on its Intelligence Index and ranks it **#1 of 216** for that index. Its reported scores include Terminal-Bench 4.0 at about 60%, SciCode at about 67%, and Humanity's Last Exam at about 61%. See the [model release/index page](https://artificialanalysis.ai/models/releases/claude-opus-5-5) and the [index methodology](https://artificialanalysis.ai/evaluations/artificial-analysis-intelligence-index).

These results cannot be compared numerically with ARIES's authored 10-question diagnostic or its cache microbenchmark: they are different tasks, measures, and execution paths. ARIES has not yet published scores for the comparable independent evaluations, so it has **no defensible rank against leading general-purpose models yet**. Its evidence currently supports a working, low-overhead deterministic fast path and live endpoint—not parity with frontier language models.

## Official leaderboard readiness

The [Hugging Face Open LLM Leaderboard submission guide](https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting) requires a public model repository, successful supported AutoClass model/tokenizer loading, Safetensors, an accurate model card, and submission of a specific revision. The GitHub checkpoint directory by itself does not satisfy the public Hugging Face model-repository requirement.

The repository's earlier readiness note records that the Hugging Face upload was blocked because GitHub Actions secret `HF_TOKEN` was not configured. Publish only after checking dataset/license provenance; add a Hugging Face **write** token as the GitHub Actions secret `HF_TOKEN` (never place it in source code, issues, or chat); then verify the public model page, run public `AutoConfig`, `AutoTokenizer`, and `AutoModelForCausalLM` loading/generation against a pinned commit, and complete an official leaderboard submission. Do not claim acceptance or rank until the board/queue confirms it.

## Next honest milestone

1. Finish the public Hub upload and pinned-revision AutoClass check after credentials and licensing are ready.
2. Run a recognized broad benchmark on the **Transformer checkpoint** rather than the n-gram API baseline; publish full results, not only a 25-example smoke test.
3. Only then request official leaderboard evaluation and compare on the same benchmark, precision, revision, prompts, and scoring protocol.

This report does not claim P=NP, a Millennium Prize proof, sub-nanosecond inference, official ranking, or parity with a frontier model.
