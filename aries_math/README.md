# ARIES unified mathematics and PRISE module

This module packages the supplied mathematical ideas as inspectable Python operators:

- Digital-root / 3-6-9 features
- Parametric torus coordinates, rotations, and surface area
- Helixo logarithmic spiral coordinates
- One-dimensional sample diagnostics inspired by spectral analysis
- Euler characteristic and a finite Euler-product approximation
- PRISE weighted problem-priority scoring
- An explicitly exponential brute-force CNF-SAT baseline for small instances

## Use

From the repository root:

```powershell
python -m unittest tests.test_prise_unified_math -v
```

Example:

```python
from aries_math.prise_unified import PRISEProblem, exact_sat_bruteforce

problem = PRISEProblem(
    name="Dispatch delay", priority=0.8, risk=0.5,
    impact=0.9, systemic=0.6, emergent=0.4
)
print(problem.to_dict())

# CNF: (x1 OR NOT x2) AND x2
print(exact_sat_bruteforce([[1, -2], [2]], variable_count=2))
```

## Scientific and performance limits

These are engineering features and research experiments, not a proof of P = NP or P != NP.
The SAT helper exhaustively enumerates assignments and therefore has exponential worst-case
runtime; it deliberately caps instances at 24 variables by default. Digital roots and geometric
coordinates are deterministic transforms, but do not by themselves reduce arbitrary computation
to constant time. The sample diagnostics are not a mathematically valid Helmholtz-Hodge
decomposition of a general vector field. The finite prime product is an approximation, not an
exact evaluation of the Riemann zeta function. The torus surface area formula applies to a ring
torus with major radius R greater than minor radius r.

No sub-nanosecond performance is asserted. Use a monotonic high-resolution timer, repeated
runs, disclosed hardware/runtime details, and end-to-end benchmarks to measure latency. The
module is an additive research package and is not yet wired into the public API request path.


## Chat integration

The native chat gateway calls `aries_math/chat_router.py` after its existing deterministic
fast path and before the character n-gram generator. Supported explicit prompts include:

- `What is the digital root of 18?`
- `Phase-8 vector 3,4`
- `Vortex 369 of 12`
- `Helixo features of 1,2,3,4`
- `Analyze binary payload: ARIES` (analyzes UTF-8 text bytes, not executable machine code)
- `PRISE score priority=0.8 risk=0.5 impact=0.9 systemic=0.6 emergent=0.4`
- `SAT JSON: {"clauses":[[1,-2],[2]],"variable_count":2}`

The chat response includes `aries_native.math_route` when one of these tools handles a request.
Unmatched prompts continue to the existing model. This is deterministic tool routing, not a claim
that the n-gram language model itself learned these operations. SAT is still exponential exhaustive
search for small instances; these features do not establish a P vs NP result.

Run tests with:

```powershell
python -m unittest tests.test_prise_chat_router tests.test_prise_unified_math -v
```
