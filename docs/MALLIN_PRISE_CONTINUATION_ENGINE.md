# Mallin–PRISE exact continuation-state engine

## Purpose

This upgrade makes the continuation-equivalence mathematics executable as a
bounded diagnostic. It does **not** claim a universal polynomial-time SAT
compression theorem.

For a parent relation (Q(u,r,Y)), where (u) is a processed prefix and
((r,Y)) is every possible continuation, define

[
u \equiv v \iff \forall r,Y,\ Q(u,r,Y)=Q(v,r,Y).
]

The number of equivalence classes is the exact minimum number of deterministic
states needed at that cut:

[
W_i=|\{Q(u,\cdot,\cdot):u\text{ is a feasible prefix}\}|,
\qquad b_i=\lceil\log_2 W_i\rceil.
]

## Implemented components

- `analyze_continuation_matrix(matrix)`: counts distinct rows in an explicit
  Boolean continuation matrix. Rows are prefixes; columns enumerate suffix
  and outside-variable assignments. First-seen state numbering is deterministic.
- `verify_signature_soundness(matrix, signatures)`: finds concrete pairs of
  prefixes that a proposed signature merges despite different continuation rows.
- `ParityAccumulator`: exact one-bit XOR accumulator.
- `ORAccumulator`: exact one-bit OR accumulator.
- Matrix input is capped at 1,000,000 cells to keep this diagnostic bounded.

## Mathematical regression cases

### Parity parent

[
Q(q_1,\ldots,q_m)=[q_1\oplus\cdots\oplus q_m=c].
]

Only accumulated parity matters, so the continuation quotient has at most two
states, independent of child count.

### Independent-clause parent

[
Q(q,Y)=\bigwedge_{j=1}^{m}(q_j\lor y_j).
]

Every distinct prefix (q_1,\ldots,q_i) induces a distinct residual function
when the corresponding (y_j) remain independently visible. Thus
(W_i=2^i). This is a lower bound for exact sequential state compression of
this relation and interface, not a lower bound for general SAT algorithms.

## Running tests

```powershell
python -m pytest -q tests/test_continuation_states.py
```

## Production integration rule

Use these summaries only where the parent relation is formally shown to depend
on the exported signature. Keep exact task routing and full-prompt cache keys
separate. Do not use digital roots, Phase-8, Helixo, or heuristic PRISE scores
as proof of Boolean equivalence or answer correctness.

The parity/OR accumulators are exact for their stated parent relations. The
explicit matrix analyzer is a finite diagnostic; generating all rows for an
implicit SAT instance may itself be exponential. A universal, efficiently
constructible polynomial-state hierarchy for arbitrary 3-CNF remains open.
