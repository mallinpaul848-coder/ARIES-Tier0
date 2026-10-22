# ARIES Tier 0 — Buyer Brief

## Product

ARIES Tier 0 is a self-hostable inference/API software baseline for teams that want to inspect, test, and operate deterministic task handlers alongside a compact local text-generation path. It includes reproducible diagnostics, API telemetry, and an experimental PRISE mathematical research toolkit.

## Why evaluate it

- **Deployment control:** a Docker-based API and documented local Windows launch paths.
- **Inspectable behavior:** deterministic handlers for supported narrow tasks, explicit API contracts, and source-level review.
- **Measured operations:** benchmark scripts record request latency percentiles, throughput, response failures, and per-case outputs.
- **Alternative-model comparison:** the same prompt set can be run against ARIES and an authorized OpenAI-compatible endpoint.
- **Research sandbox:** bounded CNF-SAT exact checks, finite-grid flow diagnostics, and finite-spectrum analysis are available with reproducible tests.
- **Evidence-first development:** test workflows and machine-readable artifacts make it possible for a prospective customer to repeat acceptance checks.

## Potential evaluation buyers

- Engineering teams evaluating self-hosted inference/API components.
- Integrators needing deterministic narrow-task handlers around a model endpoint.
- Research groups interested in reproducible finite-instance diagnostics and experimental PRISE methods.
- Organizations that want a technical proof-of-concept before discussing source licensing or custom integration.

These are candidate use cases, not existing customer commitments or validated market-size claims.

## Demonstration path

1. Inspect the public source and choose a pinned commit.
2. Run the unit and API tests.
3. Run the ARIES endpoint benchmark and save the JSON report.
4. Supply a candidate OpenAI-compatible endpoint to the manual third-party comparison workflow.
5. Have the buyer repeat the test on buyer-controlled infrastructure with its own prompts and acceptance thresholds.
6. Review license provenance, dependencies, model weights, security, and support expectations before commercial terms.

## Evidence available in the repository

- tools/aries_bench.py: API diagnostics and project-owned functional tests.
- tools/aries_alternative_benchmark.py: multi-endpoint latency/reliability/smoke comparison.
- aries_math/prize_problem_lab.py: finite-instance research diagnostics.
- tests/: automated regression and validation tests.
- .github/workflows/: repeatable test and benchmark automation.

## Commercial paths to discuss

- Paid evaluation / proof-of-concept.
- Integration and deployment services.
- Support and maintenance agreement.
- Commercial source-code license.
- Private customization or separately negotiated IP assignment.

No pricing, exclusivity, revenue, valuation, customer adoption, or transfer of IP is promised by this brief. Scope, ownership, license obligations, deliverables, acceptance tests, support, and payment milestones should be written into a signed agreement.

## Technical scope

The current native baseline is not presented as frontier-model parity. The project-authored smoke set is not an independent general intelligence benchmark. The experimental math modules do not claim to solve P vs NP, prove global Navier–Stokes regularity, or establish the Yang–Mills mass gap. Those boundaries make the evaluation more credible: prospective buyers can see what has been tested and what remains to be demonstrated.
