"""Numerical transforms for ARIES' exploratory vortex/3-6-9 framework.

The 3-6-9 and Helixo labels are framework conventions, not established
physical laws. Functions here define explicit, testable transformations.
"""
from __future__ import annotations

import cmath
import math
from typing import Iterable


def digital_root(n: int) -> int:
    """Return the base-10 digital root; zero maps to zero."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an integer")
    return 0 if n == 0 else 1 + (abs(n) - 1) % 9


def phase_369(n: int) -> int:
    """Map an integer to its digital-root phase (0..9)."""
    return digital_root(n)


def helixo_coordinates(
    t: float,
    *,
    radius: float = 1.0,
    growth: float = 0.05,
    angular_rate: float = 2.0 * math.pi / 8.0,
    phase: float = 0.0,
) -> tuple[float, float, float]:
    """Return logarithmic-spiral coordinates (x, y, z) at parameter t.

    r(t)=radius*exp(growth*t), theta(t)=phase+angular_rate*t, z=t.
    This is a defined geometric model; parameters carry no implied physical
    interpretation unless separately validated.
    """
    vals = (t, radius, growth, angular_rate, phase)
    if not all(math.isfinite(v) for v in vals):
        raise ValueError("all parameters must be finite")
    if radius < 0:
        raise ValueError("radius must be non-negative")
    r = radius * math.exp(growth * t)
    theta = phase + angular_rate * t
    return (r * math.cos(theta), r * math.sin(theta), t)


def vortex_transform(
    x: float,
    y: float,
    *,
    angle: float = 0.0,
    radial_scale: float = 1.0,
    swirl: float = 0.0,
) -> tuple[float, float]:
    """Rotate, scale, then apply a radius-preserving swirl angle.

    The swirl angle is swirl * log(1 + hypot(x,y)); all parameters are
    explicit so the transform can be reproduced and tested.
    """
    if not all(math.isfinite(v) for v in (x, y, angle, radial_scale, swirl)):
        raise ValueError("all inputs must be finite")
    if radial_scale < 0:
        raise ValueError("radial_scale must be non-negative")
    z = complex(x, y) * radial_scale
    r = abs(z)
    return cmath.rect(r, cmath.phase(z) + angle + swirl * math.log1p(r)).real, \
        cmath.rect(r, cmath.phase(z) + angle + swirl * math.log1p(r)).imag


def phase8_cycle(start: int = 0) -> tuple[int, ...]:
    """Return eight equally spaced phase indices, normalized to [0, 2π)."""
    if not isinstance(start, int) or isinstance(start, bool):
        raise TypeError("start must be an integer")
    offset = (start % 8) * (2.0 * math.pi / 8.0)
    return tuple((offset + i * 2.0 * math.pi / 8.0) % (2.0 * math.pi)
                 for i in range(8))


def digital_root_sequence(values: Iterable[int]) -> tuple[int, ...]:
    """Apply digital_root to a finite iterable of integers."""
    return tuple(digital_root(value) for value in values)
