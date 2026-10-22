"""Finite, reproducible diagnostics for ARIES prize-problem research.

These routines test finite instances and sampled data. They are not proofs of
P vs NP, Navier–Stokes global regularity, or Yang–Mills existence/mass gap.
Standard-library only.
"""
from __future__ import annotations

import itertools
import math
from typing import Any, Dict, List, Sequence, Tuple


def sat_bruteforce(clauses: Sequence[Sequence[int]], max_variables: int = 24) -> Dict[str, Any]:
    """Solve a finite CNF instance by exhaustive search; literals are signed 1-based IDs."""
    if not isinstance(max_variables, int) or isinstance(max_variables, bool) or max_variables < 0:
        raise ValueError("max_variables must be a non-negative integer")
    normalized: List[Tuple[int, ...]] = []
    highest = 0
    for clause in clauses:
        row = tuple(clause)
        for literal in row:
            if not isinstance(literal, int) or isinstance(literal, bool) or literal == 0:
                raise ValueError("literals must be non-zero integers")
            highest = max(highest, abs(literal))
        normalized.append(row)
    if highest > max_variables:
        raise ValueError(f"instance has {highest} variables; cap is {max_variables}")
    checked = 0
    for bits in itertools.product((False, True), repeat=highest):
        checked += 1
        def literal_value(lit: int) -> bool:
            value = bits[abs(lit) - 1]
            return value if lit > 0 else not value
        if all(any(literal_value(lit) for lit in clause) for clause in normalized):
            return {"satisfiable": True, "assignment": {str(i + 1): bits[i] for i in range(highest)},
                    "variables": highest, "assignments_checked": checked,
                    "method": "exhaustive_finite_instance",
                    "proof_scope": "Result applies only to the supplied finite CNF instance."}
    return {"satisfiable": False, "assignment": None, "variables": highest,
            "assignments_checked": checked, "method": "exhaustive_finite_instance",
            "proof_scope": "Result applies only to the supplied finite CNF instance."}


def _grid(name: str, values: Sequence[Sequence[float]]) -> List[List[float]]:
    grid = [[float(v) for v in row] for row in values]
    if len(grid) < 3 or len({len(row) for row in grid}) != 1 or len(grid[0]) < 3:
        raise ValueError(f"{name} must be a rectangular grid of at least 3x3")
    if any(not math.isfinite(v) for row in grid for v in row):
        raise ValueError(f"{name} values must be finite")
    return grid


def navier_stokes_sample_diagnostics(u: Sequence[Sequence[float]], v: Sequence[Sequence[float]],
                                     dx: float = 1.0, dy: float = 1.0) -> Dict[str, Any]:
    """Finite-grid centered-difference diagnostics; no PDE solver or regularity proof."""
    if not (math.isfinite(dx) and math.isfinite(dy) and dx > 0 and dy > 0):
        raise ValueError("dx and dy must be positive finite values")
    ug, vg = _grid("u", u), _grid("v", v)
    if len(ug) != len(vg) or len(ug[0]) != len(vg[0]):
        raise ValueError("u and v grids must have matching dimensions")
    ny, nx = len(ug), len(ug[0])
    div, vort = [], []
    for j in range(1, ny - 1):
        for i in range(1, nx - 1):
            dudx = (ug[j][i + 1] - ug[j][i - 1]) / (2 * dx)
            dvdy = (vg[j + 1][i] - vg[j - 1][i]) / (2 * dy)
            dvdx = (vg[j][i + 1] - vg[j][i - 1]) / (2 * dx)
            dudy = (ug[j + 1][i] - ug[j - 1][i]) / (2 * dy)
            div.append(dudx + dvdy)
            vort.append(dvdx - dudy)
    energy = math.fsum(ug[j][i] ** 2 + vg[j][i] ** 2 for j in range(ny) for i in range(nx)) / (2 * nx * ny)
    return {"grid_shape": [ny, nx], "interior_points_checked": len(div),
            "max_abs_divergence": max(map(abs, div), default=0.0),
            "mean_squared_divergence": math.fsum(x*x for x in div) / len(div),
            "mean_vorticity": math.fsum(vort) / len(vort),
            "mean_squared_vorticity": math.fsum(x*x for x in vort) / len(vort),
            "mean_kinetic_energy_density": energy,
            "diagnostic_scope": "Finite-grid numerical diagnostic only; not a proof of global smoothness."}


def yang_mills_finite_spectrum_diagnostic(eigenvalues: Sequence[float],
                                          zero_tolerance: float = 1e-10) -> Dict[str, Any]:
    """Inspect a supplied finite spectrum; does not construct continuum Yang–Mills theory."""
    if not math.isfinite(zero_tolerance) or zero_tolerance < 0:
        raise ValueError("zero_tolerance must be finite and non-negative")
    spectrum = [float(x) for x in eigenvalues]
    if not spectrum or any(not math.isfinite(x) for x in spectrum):
        raise ValueError("eigenvalues must be non-empty and finite")
    zeros = [x for x in spectrum if abs(x) <= zero_tolerance]
    positive = [x for x in spectrum if x > zero_tolerance]
    negative = [x for x in spectrum if x < -zero_tolerance]
    gap = min(positive) if positive else None
    return {"dimension_sampled": len(spectrum), "near_zero_count": len(zeros),
            "negative_eigenvalue_count": len(negative), "lowest_positive_eigenvalue": gap,
            "finite_sample_has_positive_gap": gap is not None and not negative,
            "diagnostic_scope": "Finite supplied spectrum only; not a proof of Yang–Mills existence or continuum mass gap."}


def proof_obligation_template(problem: str) -> Dict[str, Any]:
    """Return proof obligations and explicitly leave the prize problem unproved."""
    key = problem.strip().upper().replace("-", "_").replace(" ", "_")
    targets = {
        "P_VS_NP": ["Specify a uniform algorithm for a standard NP-complete problem.",
                    "Prove correctness for every input.", "Prove polynomial worst-case bit-complexity including encoding and precision costs.",
                    "State the computational model and address all input sizes."],
        "NAVIER_STOKES": ["Specify the 3D incompressible equations, domain, and initial/boundary data.",
                          "Establish global existence in the required solution class.",
                          "Prove global smoothness or provide a valid finite-time singularity construction."],
        "YANG_MILLS": ["Construct a mathematically defined quantum Yang–Mills theory in four dimensions.",
                       "Establish the required axioms and continuum limit.",
                       "Prove a strictly positive mass gap with constants independent of cutoffs."]
    }
    if key not in targets:
        raise ValueError("supported keys: P_VS_NP, NAVIER_STOKES, YANG_MILLS")
    return {"problem": key, "status": "open_research", "proof_obligations": targets[key],
            "claim_of_solution": False,
            "note": "Finite numerical experiments and completed checklists do not replace a rigorous proof."}
