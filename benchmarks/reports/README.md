# ARIES public endpoint test — 2026-10-14

**Latest verified result: PASS for the deployed native inference baseline.** This supersedes the earlier failed snapshot in the initial report.

Measured from a GitHub-hosted runner at 2026-10-14 02:51:15 UTC:

| Route | HTTP | Observed latency |
|---|---:|---:|
| `/health` | 200 | 154.78 ms |
| `/` | 200 | 146.95 ms |
| `/diagnostics` | 200 | 174.62 ms |
| `/v1/models` | 200 | 126.27 ms |

The public service reported `inference_configured: true`, model ID `aries-native-ngram`, and one listed model. All three chat-completion samples returned HTTP 200 with non-empty answers and passed their narrow assertions. Measured chat latencies were 116.29 ms, 131.01 ms, and 147.99 ms (minimum 116.29 ms; median 131.01 ms; maximum 147.99 ms).

- Raw JSON report: [2026-10-14-public-endpoint.json](2026-10-14-public-endpoint.json)
- Source workflow and downloadable evidence artifact: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503195895
- Public endpoint: https://aries-tier0-api-6qjh.onrender.com

## What this result means

The deployed software is an ARIES-owned character n-gram baseline with a deterministic task engine. The 3/3 score covers three deliberately narrow assertions (exact string response, one arithmetic result, and an API-health-check explanation). These measurements demonstrate public reachability and basic inference only. They are **not** broad language-model quality certification, an independent benchmark score, or an official leaderboard result.

The official leaderboard submission remains separate. The current native baseline is not a Transformers foundation model suitable for normal Open LLM Leaderboard submission. The experimental GPT-2-style model being trained in GitHub Actions must be published and independently loaded before any eligible external evaluation can be attempted. See [leaderboard readiness](../LEADERBOARD_READINESS.md) and the [official submission requirements](https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting).
