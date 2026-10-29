# ARIES AI / MALLIN Platform — Public Evidence Status

Last checked: 2026-10-28

This page separates repository evidence from results that still require execution or independent review. It is not a certification.

## Quantum simulation implementation

- Pull request: [#34 — Add tested quantum statevector computation module](https://github.com/mallinpaul848-coder/ARIES-Tier0/pull/34)
- Implementation: [aries_math/quantum_simulation.py](../aries_math/quantum_simulation.py)
- Unit tests: [tests/test_quantum_simulation.py](../tests/test_quantum_simulation.py)
- CI workflow: [quantum-simulation-tests.yml](../.github/workflows/quantum-simulation-tests.yml)
- Design and claims guidance: [ADAPTIVE_QUANTUM_INSPIRED_COMPUTE.md](./ADAPTIVE_QUANTUM_INSPIRED_COMPUTE.md)

The source implements a classical state-vector simulation, including state initialization, single-qubit gates, Hadamard, Pauli-X, CNOT, probability calculation, and seeded measurement sampling. The unit-test file contains six test methods for core behavior and invalid inputs.

**Scope limitation:** this is software simulation on classical hardware, not evidence of execution on physical quantum hardware or of quantum speedup.

## Public web deployment

- Frontend project: [aries-ai-mallin-chat.vercel.app](https://aries-ai-mallin-chat.vercel.app/)
- Vercel project deployment status observed on 2026-10-28: the latest production deployment was reported as `READY`.
- Existing API endpoint: [ARIES API health endpoint](https://aries-tier0-api-6qjh.onrender.com/health)
- Prepared Cloudflare Worker source: [cloudflare/aries-worker](../cloudflare/aries-worker/)

**Important:** a Vercel deployment marked READY only establishes that the frontend deployment completed. It does not prove that a live model answers chat requests, that the quantum module is exposed by the website, or that the API is continuously available. The Cloudflare Worker source is prepared in the repository but is not confirmed deployed or connected to the frontend.

## Required validation before buyer-facing performance claims

1. Run and retain the GitHub Actions quantum simulator test results.
2. Smoke-test the deployed website's actual chat endpoint with several prompts and save HTTP status, model identifier, timestamps, and latency.
3. Confirm the deployed backend and model identity; distinguish a real language-model response from fallback behavior.
4. Run repeatable benchmarks on documented hardware with fixed versions, seeds, input cases, warm-up, and repeated measurements.
5. Compare quantum-inspired/optimization routines with suitable conventional baselines on identical instances. Report correctness or objective quality, runtime, memory, and failures.
6. Publish raw results and scripts; seek independent review before describing results as third-party validated or certified.

## Claims policy

Do not describe the project as independently certified, production-scale validated, always available, or quantum-advantaged until the corresponding evidence exists. Report measured values only with the measurement method and environment.
