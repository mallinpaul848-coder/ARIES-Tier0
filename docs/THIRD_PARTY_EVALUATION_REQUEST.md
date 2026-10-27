# ARIES AI — Third-Party Evaluation Request Packet

Prepared: 2026-10-27
Project: ARIES AI / MALLIN Platform
Code repository: https://github.com/mallinpaul848-coder/ARIES-Tier0
Hosted API: https://aries-tier0-api-6qjh.onrender.com
Model Hub page: https://huggingface.co/paulmallin777/aries-core-v1

## Request

We request an independent technical evaluation of ARIES AI, with findings reported whether positive, mixed, or negative. Please confirm whether the current system is eligible for your program and what additional artifacts or access are required.

Requested evaluation areas:
1. API correctness, robustness, and error handling.
2. Reproducible latency and throughput under stated hardware, concurrency, warm/cold conditions, and request sizes.
3. Model quality on a published, fixed benchmark suite with exact versions, sample counts, scoring method, and baseline models.
4. Model/artifact provenance, model configuration, tokenizer, weights, and training-scale claims.
5. Security and operational limitations; do not treat deterministic arithmetic routing as general model reasoning.
6. Quantum-computing claims only if supported by named hardware/provider, job or circuit identifiers, raw results, and a comparable classical baseline.

## Evidence currently available

- GitHub Actions API tests passed on commit 214fb2173a091c7567076235e46c9c9c8e323ce8.
- API integration tests passed on that commit.
- RTL smoke tests passed on that commit.
- Public endpoint workflow passed: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40523515440
- The public workflow checked five HTTP/chat paths and completed a 10-case authored diagnostic benchmark. Observed mean latency was 259.889 ms, P95 was 406.56 ms, and completed request rate was 3.847 requests/second. These are small-sample results, not a production-capacity claim.
- A previous small-sample evaluation reported ARC Easy 0.32, HellaSwag 0.32, and WinoGrande 0.40 on 25 examples per task. Exploratory only; not an official leaderboard result.
- A previous PRISE reasoning matrix completed 10 of 20 cases; 10 timed out. Incomplete cases are not counted as successes.
- A previous performance suite measured small in-process Python operations at approximately 90–120 ns median and a local in-process FastAPI test at approximately 3.65 ms median. These measurements exclude network and model inference.

## Known limitations and transparency

- No independent third-party evaluation has been completed or claimed.
- No official Hugging Face leaderboard acceptance or NIST certification is claimed.
- The Hugging Face repository above is currently private and lists only .gitattributes; a public, runnable model checkpoint with weights, tokenizer, configuration, immutable revision, and license has not been verified.
- A full independent model-quality evaluation may be blocked until a reproducible model artifact or evaluator-accessible endpoint and evaluation conditions are supplied.
- No trillion-token training run is verified. Such a claim requires deduplicated/token-counted data provenance, training logs, compute records, checkpoints, and reproducible evidence.
- No actual quantum hardware run is verified.

## Suggested independent route: NIST AITE

NIST announced its Artificial Intelligence Technology Evaluation program for volunteer blind-data testing.
Program overview: https://pages.nist.gov/ai-technology-evaluation/
Program contact listed on the NIST page: aite-poc@list.nist.gov

The initial tasks announced in July 2026 focus on image analysis with large vision-language models in quantum science, genomics, and public safety. ARIES should ask NIST whether its current text/API system fits a current track or whether future task tracks are planned; eligibility is not assumed.

## Suggested public reproducibility route: Hugging Face

Hugging Face documents community evaluation results and verified results. A model repository must contain accessible artifacts and the evaluation should include task IDs, dataset revisions, values, and source logs. Verified badges require supported verification; do not label author-run scores as independent or verified.

Evaluation results: https://huggingface.co/docs/hub/eval-results
Lighteval: https://github.com/huggingface/lighteval
Open LLM Leaderboard guidance: https://github.com/huggingface/leaderboards/blob/main/docs/source/en/open_llm_leaderboard/faq.md

## Requested reviewer output

Please provide reviewer/program name and date; exact artifact/model revision evaluated; hardware and software versions; benchmark names, dataset revisions, sample counts, metrics, and baselines; raw result files and reproducible commands where possible; latency/throughput methodology, concurrency, error rate, and warm/cold separation; limitations, failures, conflicts of interest; and permission/terms for publishing results.

Status: This is a prepared request packet. It has not been sent to NIST or Hugging Face, and no external reviewer has accepted or completed an evaluation.