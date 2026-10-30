"""Python reference bridge for the ARIES deterministic harmonic filter.

This is a pure-Python reference implementation. It does not load or call the
C++ kernel; use it for API compatibility and correctness checks.
"""

from typing import Any


def compute_digital_root(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("value must be an integer")
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return 0
    remainder = value % 9
    return 9 if remainder == 0 else remainder


def is_harmonic_node(value: int) -> bool:
    return compute_digital_root(value) in (3, 6, 9)


class ARIESHarmonicBridge:
    """Bounded FIFO reference bridge; not thread-safe."""

    def __init__(self, capacity: int = 1024) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._buffer: list[int] = []

    def push(self, value: int) -> bool:
        compute_digital_root(value)  # validate type and domain
        if len(self._buffer) >= self.capacity:
            return False
        self._buffer.append(value)
        return True

    def process_next(self) -> int | None:
        if not self._buffer:
            return None
        value = self._buffer.pop(0)
        return value * compute_digital_root(value)

    def filter_prime_harmonics(self, data_stream: list[int]) -> list[dict[str, Any]]:
        results = []
        for value in data_stream:
            root = compute_digital_root(value)
            results.append({
                "input": value,
                "digital_root": root,
                "harmonic_resonance": root in (3, 6, 9),
                "weighted_score": value * root,
            })
        return results
