# Mallin–PRISE Mathematical Highlights for ARIES

**Status:** Research integration note  
**Scope:** Exact Boolean identities, exact affine projection, restricted structural cases, and open proof obligations.

This document moves the strongest results from the Mallin–PRISE investigation into the ARIES repository without presenting an unproved P-vs-NP claim as established.

## 1. What is established

### 1.1 Existential elimination is exact

For a Boolean function (F(X,y)), define its two cofactors:

\[
F_0(X)=F(X,0),\qquad F_1(X)=F(X,1).
\]

Then existentially eliminating (y) gives:

\[
\boxed{\exists y\,F(X,y)=F_0(X)\lor F_1(X).}
\]

This identity is exact for every Boolean function. Repeated existential eliminations commute:

\[
\exists y_1\exists y_2\,F
=
\exists y_2\exists y_1\,F.
\]

The identity establishes semantic correctness, not a polynomial bound on the size or cost of a chosen representation.

### 1.2 Boolean-ring polynomial form — notation matters

Work in the Boolean ring

\[
\mathcal B_n=\mathbb F_2[x_1,\ldots,x_n]/(x_i^2-x_i).
\]

Every Boolean function has a unique multilinear polynomial representation in this ring. For Boolean values (a,b\),

\[
a\lor b=a+b+ab.
\]

If the polynomial is written as

\[
F(X,y)=A(X)+yB(X),
\]

then its cofactors are (F_0=A) and (F_1=A+B). Therefore:

\[
\exists y\,F
=A\lor(A+B)
=(A)+(A+B)+A(A+B)
=\boxed{B+AB}.
\]

Equivalently, if the symbols (C_0,C_1) denote the two cofactors themselves rather than the coefficient pair (A,B), then:

\[
\exists y\,F=C_0+C_1+C_0C_1.
\]

These are the same identity under different notation. ARIES documentation and code must not mix the two conventions.

### 1.3 Residual-function count is not representation size

For

\[
G_m=\bigwedge_{i=1}^{m}(x_i\lor y_i),
\]

fixing the (x_i)'s produces residuals

\[
R_a(y)=\bigwedge_{i:a_i=0}y_i.
\]

There are (2^m) distinct residual functions, but each is represented by an (m)-bit subset mask. Thus an exponential number of distinct residuals does not by itself imply exponential description length or circuit size.

It can imply a width lower bound for a particular fixed-order deterministic branching-program model. That model-specific statement is not a lower bound against all SAT algorithms.

### 1.4 Exact affine projection is implemented

For a system of affine Boolean equations

\[
A_U U\oplus A_B B=b,
\]

Gaussian elimination pivoting on the eliminated variables (U) produces the exact constraints induced on boundary variables (B).

ARIES implements this restricted result in:

- `aries_math/prise_projection.py`
- `tests/test_prise_projection.py`
- `benchmarks/PRISE_EXACT_PROJECTION.md`

The affine-interface routine enumerates the image of a linear map using a basis of rank (r), requiring (2^r) predicate evaluations. This is polynomial when (r=O(\log N)), subject to polynomial predicate cost. The explicit rank guard is intentional.

This proves an exact polynomial-time method for the affine slice with suitable interface rank. It does not prove that arbitrary 3-CNF instances have such a low-rank affine interface.

### 1.5 Separator-based restricted cases

If a formula separates as

\[
F(A,B,S)=F_A(A,S)\land F_B(B,S),
\]

with no dependency between (A) and (B) except through (S), then

\[
\exists A\,F
=(\exists A\,F_A)\land F_B.
\]

Conditioning on all assignments to (S) requires (2^{|S|}) cases. For separator size (O(\log N)), this factor is polynomial. More generally, standard tree-decomposition dynamic programming gives a running-time dependence exponential in treewidth and polynomial in input size; logarithmic treewidth therefore gives a polynomial-time restricted class.

This is a structural restriction, not a general solution to 3-SAT.

### 1.6 Witness reconstruction is exact when projections are exact

Suppose (H(X)=\exists y F(X,y)) and a remaining assignment (a) satisfies (H(a)=1). Test (F(a,0)). If it is true, choose (y=0); otherwise choose (y=1). The definition of existential projection guarantees the second choice works when the first does not.

Repeating this process in reverse elimination order reconstructs a witness, provided each stored projection is exact and the cofactor queries are performed correctly. The final assignment must be checked against the original formula.

## 2. What is not established

The central unresolved claim is a uniform resource bound for arbitrary 3-SAT.

A complete proof would need one fixed polynomial (p) such that, for every input formula of encoding length (N):

1. Every transformation preserves exact Boolean semantics.
2. Every intermediate representation has size at most (p(N)).
3. Total computation time is at most (p(N)).
4. Peak memory, including temporary objects, is at most (p(N)).
5. Satisfying assignments can be reconstructed and verified in polynomial time.
6. Unsatisfiable instances are correctly rejected.
7. No hidden step uses exhaustive search, exponential canonicalization, or an unbounded-rank enumeration.

A recurrence such as (S_{k+1}\leq 2S_k+O(1)) permits exponential growth. Structural hashing only merges identical subcircuits; it does not discover all semantic equivalences. A local PRISE score or a good empirical benchmark does not prove a worst-case bound.

## 3. PRISE engineering plan inside ARIES

The research engine should keep exactness separate from heuristic ordering.

### Exact layer

- Validate the input encoding.
- Preserve a reference to the original formula.
- Implement exact cofactor and affine-projection operations.
- Record all substitutions and elimination steps.
- Verify every returned SAT witness against the original formula.
- Return a clear unsupported/limit-exceeded status rather than silently exceeding configured resource bounds.

### Heuristic layer

PRISE may rank candidate variables using measured or estimated features such as:

\[
P(v)=\lambda_1d(v)+\lambda_2f(v)+\lambda_3r(v)+\lambda_4g(v)+\lambda_5h(v),
\]

where degree, fill-in, predicted interface-rank growth, predicted representation growth, and boundary size are candidate features.

This score is a heuristic for choosing an order. It is not a proof that the chosen order is globally optimal or polynomially bounded.

### Evidence layer

For each run, record:

- Formula hash and variable/clause counts.
- Representation type and version.
- Elimination order.
- Per-step and peak representation size.
- Interface rank and number of enumerated states.
- Total operations, elapsed time, and peak memory.
- SAT/UNSAT result and independent witness-verification result.
- Random seed and software revision, where applicable.

Benchmarks must distinguish exact affine workloads, bounded-treewidth workloads, and general 3-CNF experiments. Do not combine them into a universal-complexity claim.

## 4. Proof ledger

| Claim | Status | Reason |
|---|---|---|
| Boolean existential elimination by OR of cofactors | Proved identity | Direct truth-functional definition |
| Boolean-ring OR polynomial identity | Proved identity | (a\lor b=a+b+ab) over the Boolean ring |
| Exact affine existential projection | Implemented restricted theorem | Gaussian elimination; exhaustive small-instance tests |
| Low-rank affine image enumeration | Exact restricted method | (2^r) image elements |
| Logarithmic-separator SAT | Restricted polynomial-time result | (2^{O(\log N)}=N^{O(1)}), with suitable decomposition |
| Exponential residual count implies exponential general SAT time | Not established; inference is invalid | Compact residual descriptions may exist |
| Polynomial growth for every arbitrary 3-CNF elimination sequence | Open | No universal invariant or proof |
| Mallin–PRISE solves arbitrary 3-SAT in polynomial time | Not proved | Requires the universal resource theorem |
| (P=NP) | Not proved | Would follow from a correct polynomial-time 3-SAT algorithm |

## 5. Immediate implementation targets

1. Add unit tests for the two polynomial notations in §1.2, including all four assignments to the two cofactors.
2. Add a reference truth-table eliminator for small Boolean circuits and compare every optimized projection routine against it.
3. Add representation-growth telemetry before experimenting with new PRISE ordering rules.
4. Add adversarial test families and publish per-family results rather than one aggregate score.
5. Keep the arbitrary-3-SAT universal polynomial-growth theorem marked **OPEN** until a complete proof is reviewed.

## 6. Scientific and commercial wording

Accurate description:

> ARIES contains an experimental Mallin–PRISE research module with exact Boolean elimination identities, an implemented affine GF(2) projection engine, and restricted structural methods. The universal polynomial-time solution of arbitrary 3-SAT remains an open research objective; no P-vs-NP proof is claimed.

Do not describe the current module as a proven P=NP solution, a universal SAT solver with polynomial worst-case complexity, or an independently certified breakthrough.
