"""Exact PRISE projection primitives for affine Boolean constraints.

This module implements only the proven affine slice of the Mallin–PRISE
projection programme. It does not claim a polynomial-time algorithm for
arbitrary 3-SAT. All vectors are represented as non-negative integer bitmasks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


@dataclass(frozen=True)
class AffineProjection:
    """Projected constraints on boundary bits after existentially removing U."""

    n_boundary: int
    equations: tuple[tuple[int, int], ...]  # (boundary coefficient mask, rhs)
    inconsistent: bool

    def accepts(self, boundary: int) -> bool:
        if boundary < 0 or boundary >= (1 << self.n_boundary):
            raise ValueError("boundary assignment is outside its declared width")
        if self.inconsistent:
            return False
        return all(((mask & boundary).bit_count() & 1) == rhs
                   for mask, rhs in self.equations)


@dataclass(frozen=True)
class InterfaceProjection:
    """Result of exact existential projection through a low-rank affine image."""

    satisfiable: bool
    witness_vector: int | None
    rank: int
    enumerated: int


def _validate_equations(
    a_u: Sequence[int], a_b: Sequence[int], rhs: Sequence[int],
    n_u: int, n_b: int,
) -> list[list[int]]:
    if n_u < 0 or n_b < 0:
        raise ValueError("variable counts must be non-negative")
    if not (len(a_u) == len(a_b) == len(rhs)):
        raise ValueError("equation arrays must have equal lengths")
    u_limit, b_limit = 1 << n_u, 1 << n_b
    rows: list[list[int]] = []
    for u_mask, b_mask, bit in zip(a_u, a_b, rhs):
        if not isinstance(u_mask, int) or not 0 <= u_mask < u_limit:
            raise ValueError("invalid eliminated-variable mask")
        if not isinstance(b_mask, int) or not 0 <= b_mask < b_limit:
            raise ValueError("invalid boundary-variable mask")
        if bit not in (0, 1):
            raise ValueError("right-hand sides must be bits")
        rows.append([u_mask, b_mask, bit])
    return rows


def eliminate_affine_variables(
    a_u: Sequence[int], a_b: Sequence[int], rhs: Sequence[int],
    n_u: int, n_b: int,
) -> AffineProjection:
    """Compute the exact projection ∃U: A_U U ⊕ A_B B = rhs.

    Each equation is encoded by a_u[i]·U XOR a_b[i]·B = rhs[i].
    Gaussian row operations pivot on U first. Rows with no remaining U
    coefficient are precisely the induced constraints on B. A second
    elimination canonicalizes those boundary constraints.
    """
    rows = _validate_equations(a_u, a_b, rhs, n_u, n_b)
    pivot_row = 0
    for column in range(n_u):
        pivot = next((i for i in range(pivot_row, len(rows))
                      if (rows[i][0] >> column) & 1), None)
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        for i in range(len(rows)):
            if i != pivot_row and ((rows[i][0] >> column) & 1):
                rows[i][0] ^= rows[pivot_row][0]
                rows[i][1] ^= rows[pivot_row][1]
                rows[i][2] ^= rows[pivot_row][2]
        pivot_row += 1

    projected = [[b_mask, bit] for u_mask, b_mask, bit in rows if u_mask == 0]
    boundary_pivot = 0
    for column in range(n_b):
        pivot = next((i for i in range(boundary_pivot, len(projected))
                      if (projected[i][0] >> column) & 1), None)
        if pivot is None:
            continue
        projected[boundary_pivot], projected[pivot] = projected[pivot], projected[boundary_pivot]
        for i in range(len(projected)):
            if i != boundary_pivot and ((projected[i][0] >> column) & 1):
                projected[i][0] ^= projected[boundary_pivot][0]
                projected[i][1] ^= projected[boundary_pivot][1]
        boundary_pivot += 1

    inconsistent = any(mask == 0 and bit == 1 for mask, bit in projected)
    equations = tuple(sorted((mask, bit) for mask, bit in projected if mask != 0))
    return AffineProjection(n_b, equations, inconsistent)


def _image_basis(matrix_rows: Sequence[int], n_inputs: int) -> list[int]:
    """Return an independent XOR basis for the column image of M."""
    if n_inputs < 0:
        raise ValueError("input width must be non-negative")
    output_width = len(matrix_rows)
    limit = 1 << n_inputs
    columns = []
    for col in range(n_inputs):
        vector = sum(((row >> col) & 1) << r for r, row in enumerate(matrix_rows))
        columns.append(vector)
    basis: dict[int, int] = {}
    for vector in columns:
        value = vector
        for pivot in sorted(basis, reverse=True):
            if (value >> pivot) & 1:
                value ^= basis[pivot]
        if value:
            pivot = value.bit_length() - 1
            basis[pivot] = value
    if any(not isinstance(row, int) or row < 0 or row >= limit for row in matrix_rows):
        raise ValueError("matrix row contains a bit outside its input width")
    if output_width < 0:
        raise ValueError("invalid output width")
    return [basis[p] for p in sorted(basis)]


def project_affine_interface(
    matrix_rows: Sequence[int], offset: int, n_inputs: int,
    predicate: Callable[[int], bool], max_rank: int = 20,
) -> InterfaceProjection:
    """Decide ∃t: predicate(Mt XOR offset) by enumerating the image of M.

    Runtime is O(2^rank · predicate_cost), not O(2^n_inputs). The explicit
    max_rank guard prevents accidental exponential blow-ups.
    """
    if max_rank < 0:
        raise ValueError("max_rank must be non-negative")
    output_width = len(matrix_rows)
    if offset < 0 or offset >= (1 << output_width):
        raise ValueError("offset is outside the output width")
    basis = _image_basis(matrix_rows, n_inputs)
    rank = len(basis)
    if rank > max_rank:
        raise ValueError(f"interface rank {rank} exceeds configured maximum {max_rank}")
    image = [0]
    for vector in basis:
        image += [value ^ vector for value in image]
    for value in image:
        candidate = value ^ offset
        if predicate(candidate):
            return InterfaceProjection(True, candidate, rank, len(image))
    return InterfaceProjection(False, None, rank, len(image))
