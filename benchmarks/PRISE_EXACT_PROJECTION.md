# PRISE Exact Projection Upgrade

This addition turns two established mathematical results from the Mallin–PRISE
investigation into executable, independently testable primitives.

## Included

- `aries_math/prise_projection.py`: exact GF(2) existential elimination and
  exact projection through a low-rank affine interface.
- `tests/test_prise_projection.py`: exhaustive small-instance comparisons
  against direct witness enumeration, including inconsistency and rank guards.
- `tools/prise_projection_bench.py`: deterministic microbenchmark reporting
  min/mean/P50/P95/max and operations per second.
- `.github/workflows/prise-projection-benchmark.yml`: CI tests and an uploaded
  benchmark artifact.

## Mathematical scope

For `A_U U XOR A_B B = b`, row reduction pivoting on the eliminated variables
produces the exact constraints on `B`. For an affine interface `M t XOR d`,
the second routine enumerates the image of `M`, requiring `2^rank(M)`
predicate evaluations. A logarithmic interface rank is sufficient for a
polynomial number of evaluations in input size.

The implementation does **not** establish that arbitrary 3-CNF has a
logarithmic affine interface, and does not claim `P = NP`. The rank guard is
intentional: it prevents silently treating an exponential interface as cheap.

## Reproduction

```bash
python -m unittest tests.test_prise_projection -v
python tools/prise_projection_bench.py --iterations 1000 --output reports/prise-projection-benchmark.json
```

The benchmark measures only these Python affine projection routines on the
declared fixed workload. It is not model inference latency, end-to-end API
latency, an HFT benchmark, or an independent certification.
