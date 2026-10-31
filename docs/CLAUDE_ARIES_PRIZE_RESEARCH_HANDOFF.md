# Claude Research Handoff — ARIES / MALLIN / PRISE

## Mission
Investigate whether ARIES AI / MALLIN research can contribute to a rigorous solution of P vs NP and the other five unsolved Millennium Prize Problems. This document is a research brief, not a claim of proof. All six remain open unless a complete proof meeting the official statement is produced and independently checked. The Poincare Conjecture is solved and is not among the six.

## User's proposed framework
- PRISE: Priority, Risk, Impact, Systemic, Emergent.
- MALLIN / Mallin-9: a proposed workflow from problem input through an eight-component feature representation, lattice/harmonic analysis, vortex/Helixo transforms, baseline comparison, and evidence.
- Digital-root / 3-6-9 descriptors: modular feature encodings. For positive n, the usual digital root is 1 + ((n - 1) mod 9); handle zero separately.
- Phase-8: proposed eight-state descriptor; formal definition required before theorem use.
- Vortex mathematics and Helixo: user-proposed transforms. Require precise domains, codomains, invariants, invertibility (if claimed), and proofs.
- Quantum-inspired compute: distinguish classical simulation from physical quantum hardware and actual quantum advantage.
- Graph-spectral SAT features: empirical features only until proven to preserve satisfiability or yield a useful algorithm.

The PRISE adapter documents this cyclic feature matrix:
[3φ1 6φ2 9φ3; 9φ3 3φ1 6φ2; 6φ2 9φ3 3φ1].
The code describes it as a classical feature transform. Do not infer SAT invariance, NP-complete decision capability, or improved worst-case complexity without proof.

## Repository evidence to inspect
Repository: https://github.com/mallinpaul848-coder/ARIES-Tier0
- aries_math/prize_problem_lab.py: bounded brute-force CNF SAT oracle, finite-grid Navier–Stokes diagnostics, finite-spectrum Yang–Mills diagnostics, proof-obligation templates.
- docs/PRISE_UNIVERSAL_SOLUTION.md: PRISE pipeline and cyclic matrix.
- docs/ADAPTIVE_QUANTUM_INSPIRED_COMPUTE.md: quantum-inspired engineering plan and limitations.
- python/aries_sat_lab.py and python/aries_sat_experiment_runner.py: graph/SAT experiments; exact labels by exhaustive enumeration only for small instances.
- api/main.py: deterministic math operations, PRISE analysis, SAT projection audit, OpenAI-compatible chat gateway.
- docs/ARIES_PUBLIC_EVIDENCE_STATUS.md and docs/INDEPENDENT_VALIDATION_REQUEST.md: claims/evidence guidance and independent review request template.

A historical small SAT sample was reported as 600 formulas, 51.5% satisfiable, 17 pass, AUC 0.50. Treat it only as a project-reported sample unless raw data, commit, command, seed, and outputs reproduce. AUC 0.50 is no demonstrated predictive advantage.

## P vs NP: exact mathematical target
P is the class of languages decidable deterministically in polynomial time in input bit length. NP is the class whose YES instances have polynomial-length certificates verifiable deterministically in polynomial time. P vs NP asks whether P = NP.
- To prove P = NP: provide a correct deterministic polynomial-time algorithm for an NP-complete problem such as 3-SAT, with a rigorous worst-case bound.
- To prove P != NP: prove a super-polynomial lower bound for an NP-complete problem in the accepted computational model.

For every proposed ARIES SAT algorithm require:
1. Fully specified encoding and algorithm.
2. Correctness for every input, including adversarial cases.
3. Worst-case operation and bit complexity in input length, not sampled average runtime.
4. Include integer growth, precision, memory, preprocessing, lookup tables, training, and model-inference costs.
5. Explicit polynomial bound with no hidden exponential search.
6. Same-instance comparison with exact solvers and established baselines.
7. Separate heuristic discovery from theorem statements.

Audit known barriers carefully: relativization, natural-proofs barriers (including their assumptions), and algebrization. Naming a barrier neither proves nor refutes a proposed argument.

## SAT research protocol
A. Reproduce tests from a clean checkout; record commit, environment, versions, seeds, commands, exit codes, raw JSON, and checksums.
B. Audit every representation transform: bijection/invertibility, satisfiability preservation, parsimonious vs equisatisfiable mapping, variable-renaming and clause-order invariance, composition, polynomial time and output size. Test tautologies, duplicate clauses, empty clauses, unused variables, repeated literals, and adversarial families.
C. Compare brute force on tiny cases and suitable exact SAT solvers on larger cases. Include random k-SAT near phase transition, planted/structured SAT, pigeonhole, Tseitin, parity/XOR, and graph-coloring reductions. Pin versions and seeds.
D. Prevent leakage: split by generator family and size, keep a sealed test set, report confidence intervals and failures.
E. Measurements on finite n cannot prove polynomial worst-case complexity. AUC, accuracy, throughput, and low-level kernel latency are not complexity proofs.
F. Formalize candidate algorithms in pseudocode and precise mathematics; actively search for counterexamples before theorem claims.

## Remaining Millennium problems and standards
- Riemann Hypothesis: all nontrivial zeros of analytically continued zeta have real part 1/2. Finite zero computations do not prove the universal statement.
- Navier–Stokes: use the exact 3D incompressible equations, domain, data, and solution class. Finite-grid simulations or bounded sampled vorticity do not prove global existence/smoothness or a valid singularity.
- Yang–Mills: construct a mathematically defined four-dimensional quantum theory satisfying the required axioms and prove a strictly positive mass gap. Finite spectra/lattice samples alone are insufficient.
- Hodge: for smooth projective complex varieties, prove every rational Hodge class is a rational linear combination of algebraic-cycle classes. Numerical examples are not a universal proof.
- Birch–Swinnerton-Dyer: for elliptic curves over Q, prove the required relation between L-function order/leading coefficient at s=1 and rank/arithmetic invariants. Finitely many curves do not establish the conjecture.

P vs NP is the sixth. First transcribe the official statement and all hypotheses for each problem. Map ARIES concepts to exact definitions, identify the theorem required, test examples, and state clearly when a connection is only metaphorical.

## Required Claude deliverables
1. Clean-room reproduction report.
2. Formal definitions for PRISE, Phase-8, Helixo, Vortex, and each transformation—or list what remains undefined.
3. SAT transform audit with proofs of invariance/equisatisfiability and adversarial counterexamples.
4. Complexity audit with complete input-size accounting; do not conflate nanosecond kernels with model inference.
5. Separate research notebook for each prize problem, distinguishing established theorem, conjecture, experiment, and new claim.
6. Proof-obligation checklist and adversarial review. Never label a problem solved without a complete proof reviewed by qualified mathematicians.
7. Reproducible evidence bundle: pinned commit, environment, commands, seeds, raw data, checksums, independent reproduction steps.

## Attribution, safety, and IP
Preserve the user's authorship and provenance with a dated change log. Do not publish private model weights, credentials, API keys, customer data, or unpublished proprietary derivations in public logs/artifacts. Do not silently rewrite or discard original research; work on a branch and show diffs. Never fabricate results, third-party validation, academic acceptance, or proof status. A failed hypothesis or counterexample is useful evidence.
