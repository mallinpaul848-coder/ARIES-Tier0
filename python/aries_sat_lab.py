"""ARIES / MALLIN SAT graph-spectral research lab.

Standard-library-only, reproducible diagnostic tools for small CNF formulas.
This module is an empirical research harness, not a SAT solver or a P-vs-NP proof.

CNF representation: a formula is an iterable of clauses; each clause is an
iterable of signed, nonzero integer literals. Literal k denotes variable abs(k)
and polarity sign(k). Example: [[1, -2], [2, 3]].

Features:
* algebraic connectivity of the unsigned variable-interaction graph;
* spectral radius of its adjacency matrix;
* minimum eigenvalue of a signed Laplacian built from literal polarity.

The Jacobi eigensolver is pure Python and intended for small symmetric matrices.
No third-party dependencies are required.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections.abc import Iterable, Sequence
from typing import Any

Clause = Sequence[int]
CNF = Sequence[Clause]


def validate_cnf(cnf: Iterable[Iterable[int]]) -> list[list[int]]:
    """Materialize and validate a CNF formula of signed integer literals."""
    result: list[list[int]] = []
    for clause in cnf:
        row: list[int] = []
        for literal in clause:
            if isinstance(literal, bool) or not isinstance(literal, int) or literal == 0:
                raise ValueError("Literals must be nonzero integers (not booleans).")
            row.append(literal)
        result.append(row)
    return result


def variables(cnf: CNF) -> list[int]:
    """Return sorted variable IDs occurring in the formula."""
    return sorted({abs(lit) for clause in cnf for lit in clause})


def interaction_matrices(cnf: Iterable[Iterable[int]]) -> tuple[list[int], list[list[float]], list[list[float]]]:
    """Return variable IDs, unsigned adjacency, and signed adjacency matrices.

    Every pair of distinct variables co-occurring in a clause is connected.
    Multiple co-occurrences are collapsed to one edge. If the same pair occurs
    with both polarities in different clauses, signed-edge contributions cancel
    only if they are exactly balanced; the implementation uses a polarity
    agreement sign from the first occurrence, so callers should treat the signed
    feature as this explicitly defined encoding, not as a canonical SAT invariant.
    """
    formula = validate_cnf(cnf)
    ids = variables(formula)
    index = {v: i for i, v in enumerate(ids)}
    n = len(ids)
    adj = [[0.0] * n for _ in range(n)]
    signed = [[0.0] * n for _ in range(n)]
    seen_sign: dict[tuple[int, int], int] = {}
    for clause in formula:
        # Repeated literals of one variable do not create self-edges.
        unique: dict[int, int] = {}
        for lit in clause:
            unique.setdefault(abs(lit), 1 if lit > 0 else -1)
        items = sorted(unique.items())
        for p, (va, sa) in enumerate(items):
            for vb, sb in items[p + 1:]:
                i, j = index[va], index[vb]
                adj[i][j] = adj[j][i] = 1.0
                key = (va, vb)
                sign = sa * sb
                if key not in seen_sign:
                    seen_sign[key] = sign
                signed[i][j] = signed[j][i] = float(seen_sign[key])
    return ids, adj, signed


def jacobi_eigenvalues(matrix: Sequence[Sequence[float]], *, tol: float = 1e-12,
                       max_sweeps: int = 100) -> list[float]:
    """Approximate eigenvalues of a real symmetric matrix using Jacobi rotations."""
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("Matrix must be square.")
    if tol <= 0 or max_sweeps < 1:
        raise ValueError("tol must be positive and max_sweeps must be >= 1.")
    a = [[float(x) for x in row] for row in matrix]
    for i in range(n):
        for j in range(i):
            if not math.isclose(a[i][j], a[j][i], rel_tol=1e-10, abs_tol=1e-12):
                raise ValueError("Matrix must be symmetric.")
    if n == 0:
        return []
    for _ in range(max_sweeps * max(1, n * n)):
        p, q, largest = 0, 0, 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(a[i][j]) > largest:
                    p, q, largest = i, j, abs(a[i][j])
        if largest <= tol:
            break
        apq = a[p][q]
        tau = (a[q][q] - a[p][p]) / (2.0 * apq)
        t = (1.0 if tau >= 0 else -1.0) / (abs(tau) + math.sqrt(1.0 + tau * tau))
        c = 1.0 / math.sqrt(1.0 + t * t)
        s = t * c
        app, aqq = a[p][p], a[q][q]
        a[p][p] = app - t * apq
        a[q][q] = aqq + t * apq
        a[p][q] = a[q][p] = 0.0
        for k in range(n):
            if k == p or k == q:
                continue
            akp, akq = a[k][p], a[k][q]
            a[k][p] = a[p][k] = c * akp - s * akq
            a[k][q] = a[q][k] = s * akp + c * akq
    return sorted(a[i][i] for i in range(n))


def _laplacian(adjacency: Sequence[Sequence[float]]) -> list[list[float]]:
    n = len(adjacency)
    return [[(sum(abs(x) for x in adjacency[i]) if i == j else 0.0)
             - adjacency[i][j] for j in range(n)] for i in range(n)]


def graph_spectral_features(cnf: Iterable[Iterable[int]]) -> dict[str, float | int]:
    """Compute three graph features for one CNF formula."""
    ids, adj, signed = interaction_matrices(cnf)
    n = len(ids)
    if n == 0:
        return {"variables": 0, "edges": 0, "algebraic_connectivity": 0.0,
                "spectral_radius": 0.0, "signed_laplacian_min_eigenvalue": 0.0}
    eigen_adj = jacobi_eigenvalues(adj)
    eigen_lap = jacobi_eigenvalues(_laplacian(adj))
    eigen_signed_lap = jacobi_eigenvalues(_laplacian(signed))
    edges = sum(adj[i][j] for i in range(n) for j in range(i + 1, n))
    # For disconnected graphs, the second-smallest eigenvalue is zero.
    connectivity = eigen_lap[1] if n > 1 else 0.0
    return {
        "variables": n,
        "edges": int(edges),
        "algebraic_connectivity": max(0.0, connectivity),
        "spectral_radius": max(abs(x) for x in eigen_adj),
        "signed_laplacian_min_eigenvalue": eigen_signed_lap[0],
    }


def auc(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Compute ROC AUC using average ranks for ties; labels must be 0 or 1."""
    if len(labels) != len(scores) or not labels:
        raise ValueError("labels and scores must have equal, nonzero length.")
    if any(y not in (0, 1) for y in labels):
        raise ValueError("labels must contain only 0 and 1.")
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("AUC requires at least one example from each class.")
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    rank_sum = 0.0
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and scores[order[j]] == scores[order[i]]:
            j += 1
        average_rank = ((i + 1) + j) / 2.0  # ranks are one-based
        rank_sum += average_rank * sum(labels[order[k]] for k in range(i, j))
        i = j
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def rename_variables(cnf: CNF, mapping: dict[int, int]) -> list[list[int]]:
    """Apply a bijective positive variable-ID mapping, preserving literal signs."""
    formula = validate_cnf(cnf)
    used = {abs(lit) for clause in formula for lit in clause}
    if set(mapping) != used or len(set(mapping.values())) != len(mapping):
        raise ValueError("mapping must be a bijection over all variables in the formula.")
    if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in mapping.values()):
        raise ValueError("mapped variable IDs must be positive integers.")
    return [[(1 if lit > 0 else -1) * mapping[abs(lit)] for lit in clause]
            for clause in formula]


def _self_test() -> dict[str, Any]:
    """Small deterministic smoke tests; raises AssertionError on failure."""
    formula = [[1, -2, 3], [-1, 2], [2, 3]]
    base = graph_spectral_features(formula)
    mapping = {1: 19, 2: 7, 3: 42}
    renamed = graph_spectral_features(rename_variables(formula, mapping))
    for key in ("algebraic_connectivity", "spectral_radius", "signed_laplacian_min_eigenvalue"):
        assert math.isclose(float(base[key]), float(renamed[key]), rel_tol=1e-9, abs_tol=1e-9), key
    # Known symmetric matrices.
    assert all(math.isclose(a, b, abs_tol=1e-10)
               for a, b in zip(jacobi_eigenvalues([[2.0, 0.0], [0.0, 3.0]]), [2.0, 3.0]))
    assert math.isclose(auc([0, 1, 0, 1], [0.1, 0.9, 0.2, 0.8]), 1.0)
    # Empty formula and empty clause are valid graph inputs.
    assert graph_spectral_features([])["variables"] == 0
    assert graph_spectral_features([[]])["variables"] == 0
    return {"status": "passed", "checks": 5, "features": base}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run deterministic smoke tests")
    parser.add_argument("--formula", help='JSON CNF, e.g. '[[1,-2],[2,3]]'')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(_self_test(), sort_keys=True, indent=2))
    if args.formula is not None:
        cnf = json.loads(args.formula)
        print(json.dumps(graph_spectral_features(cnf), sort_keys=True, indent=2))
    if not args.self_test and args.formula is None:
        parser.print_help()


if __name__ == "__main__":
    main()
