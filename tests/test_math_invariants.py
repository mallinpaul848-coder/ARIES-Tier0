import math

import pytest

from math_core.millennium_invariants import (
    finite_difference_curl_z,
    finite_difference_divergence,
    laplacian_2d,
    rotational_field,
)
from math_core.vortex_transforms import (
    digital_root,
    digital_root_sequence,
    helixo_coordinates,
    phase8_cycle,
    vortex_transform,
)


def test_digital_root_cycle_and_sign():
    assert [digital_root(n) for n in range(1, 10)] == list(range(1, 10))
    assert [digital_root(n) for n in (9, 18, 27, 36, 45)] == [9] * 5
    assert digital_root(0) == 0
    assert digital_root(-19) == 1
    assert digital_root_sequence([1, 2, 3, 9, 10]) == (1, 2, 3, 9, 1)


def test_helixo_radius_and_height():
    t, radius, growth, rate, phase = 2.5, 1.7, 0.08, math.pi / 4, 0.3
    x, y, z = helixo_coordinates(t, radius=radius, growth=growth,
                                 angular_rate=rate, phase=phase)
    assert math.isclose(math.hypot(x, y), radius * math.exp(growth * t),
                        rel_tol=1e-12)
    assert z == t


def test_vortex_transform_radius_and_rotation():
    x, y = 3.0, 4.0
    tx, ty = vortex_transform(x, y, angle=math.pi / 2, radial_scale=2.0)
    assert math.isclose(math.hypot(tx, ty), 10.0, rel_tol=1e-12)
    assert math.isclose(tx, -8.0, abs_tol=1e-12)
    assert math.isclose(ty, 6.0, abs_tol=1e-12)


def test_phase8_cycle():
    phases = phase8_cycle()
    assert len(phases) == 8
    assert math.isclose(phases[0], 0.0, abs_tol=1e-12)
    assert math.isclose(phases[-1], 7 * math.pi / 4, abs_tol=1e-12)


def test_regularized_vortex_divergence():
    field = lambda x, y: rotational_field(x, y, epsilon=0.1)
    for x, y in ((0.3, 0.7), (1.2, -0.4), (-0.8, 0.5)):
        assert abs(finite_difference_divergence(field, x, y)) < 2e-5


def test_finite_difference_operators():
    # For u=x^2+y^2: Laplacian is exactly 4; for field (-y, x), curl_z=2.
    field = lambda x, y: (-y, x)
    assert math.isclose(finite_difference_curl_z(field, 0.2, -0.4), 2.0,
                        rel_tol=1e-8, abs_tol=1e-8)
    assert abs(finite_difference_divergence(field, 0.2, -0.4)) < 1e-8
    scalar = lambda x, y: x*x + y*y
    assert math.isclose(laplacian_2d(scalar, 0.4, -0.9), 4.0,
                        rel_tol=1e-5, abs_tol=1e-5)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        helixo_coordinates(1.0, radius=-1)
    with pytest.raises(ValueError):
        vortex_transform(1, 2, radial_scale=-1)
    with pytest.raises(ValueError):
        rotational_field(1, 2, epsilon=0)
    with pytest.raises(TypeError):
        digital_root(2.5)
