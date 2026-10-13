# ARIES Tier 0 v1.0 — External Testing Status

## What this workflow tests
GitHub Actions compiles the Verilog RTL using Icarus Verilog and runs a deterministic smoke test for reset behavior, trigger capture, and lock clearing.

## What this does not establish
- It does not verify physical hardware, a 4 GHz clock, sub-nanosecond silicon performance, or formal equivalence.
- It does not benchmark a language model.
- A passing GitHub Actions run is third-party-hosted CI execution, not independent model evaluation or a leaderboard result.

## Public inference endpoint
No live inference endpoint is configured in this repository at this time. A public endpoint requires a running model server and a reachable HTTPS host. Do not publish an endpoint URL or claim model benchmark results until the deployed service is reachable and tested.

## Next verification steps
1. Open the repository Actions page and inspect the latest workflow run.
2. Confirm the RTL smoke test job reports success.
3. Configure a real model server and a public HTTPS endpoint separately.
4. Run external API checks against the deployed endpoint and retain the measured output.
