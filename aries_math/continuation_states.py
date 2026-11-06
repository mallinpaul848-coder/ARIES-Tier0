"""Exact continuation-state diagnostics for Mallin–PRISE compression.

This module turns the residual-function mathematics into executable, bounded
diagnostics. A row represents the output of a parent relation for one processed
prefix over every enumerated suffix. Equal rows are exactly equivalent for
that finite continuation domain.

This is a diagnostic for explicit finite tables, not a general SAT solver and
not a proof that arbitrary 3-SAT instances have polynomially many states.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2
from typing import Hashable, Sequence


@dataclass(frozen=True)
class ContinuationQuotient:
    """Canonical first-seen quotient of the rows of a Boolean matrix."""

    prefix_to_state: tuple[int, ...]
    representative_prefixes: tuple[int, ...]
    state_count: int
    state_bits: int
    prefix_count: int
    suffix_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "prefix_to_state": list(self.prefix_to_state),
            "representative_prefixes": list(self.representative_prefixes),
            "state_count": self.state_count,
            "minimum_state_bits": self.state_bits,
            "prefix_count": self.prefix_count,
            "suffix_count": self.suffix_count,
            "equivalence": "two prefixes share a state iff their enumerated continuation rows are identical",
        }


def _validated_matrix(matrix: Sequence[Sequence[int | bool]]) -> tuple[tuple[int, ...], ...]:
    if not isinstance(matrix, (list, tuple)) or not matrix:
        raise ValueError("matrix must contain at least one prefix row")
    rows: list[tuple[int, ...]] = []
    width: int | None = None
    total_cells = 0
    for row_index, row in enumerate(matrix):
        if not isinstance(row, (list, tuple)):
            raise ValueError(f"row {row_index} must be a list or tuple")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError("matrix must be rectangular")
        parsed: list[int] = []
        for col_index, value in enumerate(row):
            if isinstance(value, bool):
                parsed.append(int(value))
            elif isinstance(value, int) and value in (0, 1):
                parsed.append(value)
            else:
                raise ValueError(f"matrix[{row_index}][{col_index}] must be Boolean or 0/1")
        total_cells += len(parsed)
        if total_cells > 1_000_000:
            raise ValueError("matrix exceeds the 1,000,000-cell diagnostic limit")
        rows.append(tuple(parsed))
    return tuple(rows)


def analyze_continuation_matrix(
    matrix: Sequence[Sequence[int | bool]],
) -> ContinuationQuotient:
    """Count exact continuation classes in an explicitly supplied Boolean matrix.

    Rows correspond to processed prefixes; columns correspond to suffix
    assignments (and, if needed, outside-variable assignments). The function
    does not generate the matrix and therefore makes no claim that constructing
    a large implicit matrix is efficient.
    """
    rows = _validated_matrix(matrix)
    row_to_state: dict[tuple[int, ...], int] = {}
    prefix_to_state: list[int] = []
    representatives: list[int] = []
    for prefix_index, row in enumerate(rows):
        state = row_to_state.get(row)
        if state is None:
            state = len(row_to_state)
            row_to_state[row] = state
            representatives.append(prefix_index)
        prefix_to_state.append(state)
    count = len(row_to_state)
    return ContinuationQuotient(
        prefix_to_state=tuple(prefix_to_state),
        representative_prefixes=tuple(representatives),
        state_count=count,
        state_bits=ceil(log2(count)) if count > 1 else 0,
        prefix_count=len(rows),
        suffix_count=len(rows[0]),
    )


def verify_signature_soundness(
    matrix: Sequence[Sequence[int | bool]],
    signatures: Sequence[Hashable],
) -> dict[str, object]:
    """Check whether equal proposed signatures ever merge distinct rows."""
    rows = _validated_matrix(matrix)
    if not isinstance(signatures, (list, tuple)) or len(signatures) != len(rows):
        raise ValueError("one hashable signature is required for every prefix")
    seen: dict[Hashable, tuple[int, tuple[int, ...]]] = {}
    violations: list[dict[str, int]] = []
    for index, (signature, row) in enumerate(zip(signatures, rows)):
        try:
            previous = seen.get(signature)
        except TypeError as exc:
            raise ValueError("each signature must be hashable") from exc
        if previous is None:
            seen[signature] = (index, row)
        elif previous[1] != row:
            violations.append({
                "first_prefix": previous[0],
                "second_prefix": index,
            })
    return {
        "sound": not violations,
        "violation_count": len(violations),
        "violations": violations,
        "signature_class_count": len(seen),
        "exact_continuation_class_count": analyze_continuation_matrix(rows).state_count,
    }


class ParityAccumulator:
    """One-bit exact accumulator for XOR parent constraints."""

    def __init__(self, initial: int | bool = 0) -> None:
        self._state = self._bit(initial, "initial")

    @staticmethod
    def _bit(value: int | bool, name: str) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int) and value in (0, 1):
            return value
        raise ValueError(f"{name} must be Boolean or 0/1")

    @property
    def state(self) -> int:
        return self._state

    def update(self, bit: int | bool) -> int:
        self._state ^= self._bit(bit, "bit")
        return self._state


class ORAccumulator:
    """One-bit exact accumulator for a monotone OR parent constraint."""

    def __init__(self, initial: int | bool = 0) -> None:
        self._state = ParityAccumulator._bit(initial, "initial")

    @property
    def state(self) -> int:
        return self._state

    def update(self, bit: int | bool) -> int:
        self._state |= ParityAccumulator._bit(bit, "bit")
        return self._state
