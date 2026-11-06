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



def solve_gf2(
    matrix: Sequence[Sequence[int | bool]],
    rhs: Sequence[int | bool],
) -> dict[str, object]:
    """Solve A*x=b over GF(2), returning rank, one solution, and nullspace basis."""
    if not isinstance(matrix, (list, tuple)) or not matrix:
        raise ValueError("matrix must contain at least one row")
    if not isinstance(rhs, (list, tuple)) or len(rhs) != len(matrix):
        raise ValueError("rhs must contain one bit per matrix row")
    width = len(matrix[0]) if isinstance(matrix[0], (list, tuple)) else -1
    if width < 1 or width > 256:
        raise ValueError("GF(2) matrix must have between 1 and 256 columns")
    rows: list[list[int]] = []
    for i, row in enumerate(matrix):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError("GF(2) matrix must be rectangular")
        rows.append([ParityAccumulator._bit(v, f"matrix[{i}]") for v in row]
                    + [ParityAccumulator._bit(rhs[i], f"rhs[{i}]")])
    pivot_columns: list[int] = []
    pivot_row = 0
    for col in range(width):
        pivot = next((r for r in range(pivot_row, len(rows)) if rows[r][col]), None)
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        for r in range(len(rows)):
            if r != pivot_row and rows[r][col]:
                rows[r] = [a ^ b for a, b in zip(rows[r], rows[pivot_row])]
        pivot_columns.append(col)
        pivot_row += 1
        if pivot_row == len(rows):
            break
    for row in rows:
        if not any(row[:width]) and row[width]:
            return {
                "consistent": False,
                "rank": len(pivot_columns),
                "variable_count": width,
                "particular_solution": None,
                "nullspace_basis": [],
            }
    particular = [0] * width
    for r, col in enumerate(pivot_columns):
        particular[col] = rows[r][width]
    free_columns = [c for c in range(width) if c not in pivot_columns]
    basis: list[list[int]] = []
    for free in free_columns:
        vector = [0] * width
        vector[free] = 1
        for r, pivot_col in enumerate(pivot_columns):
            vector[pivot_col] = rows[r][free]
        basis.append(vector)
    return {
        "consistent": True,
        "rank": len(pivot_columns),
        "variable_count": width,
        "free_variable_count": len(free_columns),
        "particular_solution": particular,
        "nullspace_basis": basis,
        "solution_form": "x = particular_solution XOR any linear combination of nullspace_basis",
    }


def induced_width(
    adjacency: dict[Hashable, Sequence[Hashable]],
    order: Sequence[Hashable],
) -> dict[str, object]:
    """Compute induced width for a supplied variable-elimination order."""
    if not isinstance(adjacency, dict):
        raise ValueError("adjacency must be a dictionary")
    if len(adjacency) > 4096:
        raise ValueError("graph exceeds the 4,096-vertex diagnostic limit")
    vertices = set(adjacency)
    graph: dict[Hashable, set[Hashable]] = {v: set() for v in vertices}
    edge_entries = 0
    for vertex, neighbors in adjacency.items():
        if not isinstance(neighbors, (list, tuple, set)):
            raise ValueError("each adjacency entry must be a list, tuple, or set")
        edge_entries += len(neighbors)
        if edge_entries > 1_000_000:
            raise ValueError("graph exceeds the 1,000,000-edge-entry diagnostic limit")
        for neighbor in neighbors:
            if neighbor not in vertices or neighbor == vertex:
                raise ValueError("neighbors must be distinct vertices in adjacency")
            graph[vertex].add(neighbor)
            graph[neighbor].add(vertex)
    if len(order) != len(vertices) or set(order) != vertices:
        raise ValueError("order must contain every graph vertex exactly once")
    steps: list[dict[str, object]] = []
    width = 0
    for vertex in order:
        remaining = sorted(graph[vertex], key=repr)
        width = max(width, len(remaining))
        steps.append({"variable": repr(vertex), "remaining_neighbors": len(remaining)})
        for i, left in enumerate(remaining):
            for right in remaining[i + 1:]:
                graph[left].add(right)
                graph[right].add(left)
        for neighbor in remaining:
            graph[neighbor].discard(vertex)
        graph[vertex].clear()
    return {
        "induced_width": width,
        "elimination_steps": steps,
        "interpretation": "exact variable-elimination width for the supplied graph and order",
    }
