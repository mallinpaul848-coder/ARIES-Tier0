"""Small numerical diagnostics for exploratory field equations.

These are computational sanity checks, not solutions or proofs of any
Millennium Prize Problem. Navier-Stokes regularity, RH, P vs NP, Hodge, and
Yang-Mills mass gap remain open problems.
"""
from __future__ import annotations

import math
from typing import Callable


def rotational_field(x: float, y: float, epsilon: float = 1e-9) -> tuple[float, float]:
    """Smooth regularized planar vortex: (-y/(r²+eps), x/(r²+eps))."""
    if epsilon <= 0 or not math.isfinite(epsilon):
        raise ValueError("epsilon must be positive and finite")
    d = x * x + y * y + epsilon
    return -y / d, x / d


def finite_difference_divergence(
    field: Callable[[float, float], tuple[float, float]],
    x: float,
    y: float,
    h: float = 1e-5,
) -> float:
    """Central-difference estimate of ∂u/∂x + ∂v/∂y."""
    if h <= 0 or not math.isfinite(h):
        raise ValueError("h must be positive and finite")
    ux1, _ = field(x + h, y)
    ux0, _ = field(x - h, y)
    _, vy1 = field(x, y + h)
    _, vy0 = field(x, y - h)
    return (ux1 - ux0 + vy1 - vy0) / (2.0 * h)


def finite_difference_curl_z(
    field: Callable[[float, float], tuple[float, float]],
    x: float,
    y: float,
    h: float = 1e-5,
) -> float:
    """Central-difference estimate of planar curl ∂v/∂x - ∂u/∂y."""
    if h <= 0 or not math.isfinite(h):
        raise ValueError("h must be positive and finite")
    _, vx1 = field(x + h, y)
    _, vx0 = field(x - h, y)
    uy1, _ = field(x, y + h)
    uy0, _ = field(x, y - h)
    return (vx1 - vx0 - uy1 + uy0) / (2.0 * h)


def laplacian_2d(
    scalar: Callable[[float, float], float],
    x: float,
    y: float,
    h: float = 1e-4,
) -> float:
    """Five-point finite-difference Laplacian of a scalar function."""
    if h <= 0 or not math.isfinite(h):
        raise ValueError("h must be positive and finite")
    center = scalar(x, y)
    return (scalar(x + h, y) + scalar(x - h, y)
            + scalar(x, y + h) + scalar(x, y - h) - 4.0 * center) / (h * h)
