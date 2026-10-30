import pytest

from math_core.aries_harmonic_bridge import (
    ARIESHarmonicBridge,
    compute_digital_root,
    is_harmonic_node,
)


def test_digital_root_boundaries_and_large_values():
    assert [compute_digital_root(n) for n in range(10)] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert compute_digital_root(18) == 9
    assert compute_digital_root(2**64 - 1) == (2**64 - 1) % 9 or compute_digital_root(2**64 - 1) == 9


def test_harmonic_filter_is_divisibility_class_not_prime_test():
    assert is_harmonic_node(3)
    assert is_harmonic_node(6)
    assert is_harmonic_node(9)
    assert is_harmonic_node(12)
    assert not is_harmonic_node(2)
    assert not is_harmonic_node(5)


def test_invalid_values():
    with pytest.raises(TypeError):
        compute_digital_root(2.5)
    with pytest.raises(TypeError):
        compute_digital_root(True)
    with pytest.raises(ValueError):
        compute_digital_root(-1)


def test_bounded_fifo_and_weighted_score():
    bridge = ARIESHarmonicBridge(capacity=2)
    assert bridge.process_next() is None
    assert bridge.push(3)
    assert bridge.push(10)
    assert not bridge.push(12)
    assert bridge.process_next() == 9
    assert bridge.process_next() == 10
    assert bridge.process_next() is None


def test_filter_results():
    bridge = ARIESHarmonicBridge()
    assert bridge.filter_prime_harmonics([2, 3, 10]) == [
        {"input": 2, "digital_root": 2, "harmonic_resonance": False, "weighted_score": 4},
        {"input": 3, "digital_root": 3, "harmonic_resonance": True, "weighted_score": 9},
        {"input": 10, "digital_root": 1, "harmonic_resonance": False, "weighted_score": 10},
    ]


def test_capacity_must_be_positive():
    with pytest.raises(ValueError):
        ARIESHarmonicBridge(capacity=0)
