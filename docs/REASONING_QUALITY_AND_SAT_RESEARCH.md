# ARIES reasoning quality and bounded SAT research

This evaluation layer makes the PRISE / Mallin research ideas testable instead of assuming they improve reasoning. It uses the existing digital-root, vortex-369, and Phase-8 operators to build an inspectable signature, labels small CNF formulas with exact exhaustive search, and measures held-out signature lookup against a majority-class baseline.

## Run

```bash
python -m pytest -q tests/test_sat_quality_lab.py
python tools/aries_sat_quality_bench.py --count 100 --variables 8 --seed 7 --output reports/aries-sat-quality.json
```

The report includes a reproducibility fingerprint, train/test counts, accuracy, balanced accuracy, majority baseline, and signatures that collide across SAT and UNSAT examples. Re-run with multiple seeds and distributions before interpreting any trend. A score at or below baseline is evidence that this representation has not shown benefit in that experiment; it should not be promoted into a decision path merely because it uses PRISE or 3/6/9 terminology.

## Engineering policy

- Keep exact, auditable algorithms on supported narrow tasks; abstain when the deterministic solver cannot establish an answer.
- Treat PRISE, digital-root, 3/6/9, vortex, Phase-8, and Helixo values as candidate descriptors, not proof shortcuts.
- Compare changes against a baseline on held-out cases, with repeated seeds and recorded environment.
- Keep inference latency, feature-computation latency, SAT search time, and public network latency as separate metrics.
- Do not replace a correct path with an experimental heuristic unless measured quality improves without unacceptable latency or reliability regressions.

## Limits

The SAT labels are exact only because this lab exhaustively enumerates assignments. Runtime grows exponentially with variable count; the default hard cap is 16 variables. The learned signature lookup is a simple baseline, not a production SAT solver. Results depend on the generated formula distribution and do not establish worst-case complexity, P = NP, P != NP, or any Millennium Prize result. Timer units in nanoseconds do not imply sub-nanosecond execution.