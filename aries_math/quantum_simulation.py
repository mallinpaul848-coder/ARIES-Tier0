"""Small, auditable state-vector simulator for quantum-computation experiments.

This is a classical simulator for small circuits, not quantum hardware and not a
claim of quantum advantage. It deliberately contains no proprietary PRISE/MALLIN
formulae; integrations should pass reviewed inputs and compare against baselines.
"""
from __future__ import annotations

import math
import random
from typing import Sequence

Complex = complex


def _validate_state(state: Sequence[Complex], atol: float = 1e-9) -> list[Complex]:
    vector = [complex(x) for x in state]
    if not vector or len(vector) & (len(vector) - 1):
        raise ValueError("state length must be a non-zero power of two")
    if not all(math.isfinite(z.real) and math.isfinite(z.imag) for z in vector):
        raise ValueError("state amplitudes must be finite")
    norm = sum(abs(z) ** 2 for z in vector)
    if abs(norm - 1.0) > atol:
        raise ValueError("state vector must be normalized")
    return vector


def zero_state(qubits: int) -> list[Complex]:
    if not isinstance(qubits, int) or qubits < 1:
        raise ValueError("qubits must be a positive integer")
    state = [0j] * (1 << qubits)
    state[0] = 1 + 0j
    return state


def apply_single_qubit(
    state: Sequence[Complex], gate: Sequence[Sequence[Complex]], target: int
) -> list[Complex]:
    """Apply a 2x2 gate; target 0 is the least-significant qubit."""
    vector = _validate_state(state)
    n = (len(vector)).bit_length() - 1
    if not isinstance(target, int) or not 0 <= target < n:
        raise ValueError("target qubit is out of range")
    if len(gate) != 2 or any(len(row) != 2 for row in gate):
        raise ValueError("gate must be 2x2")
    a, b = complex(gate[0][0]), complex(gate[0][1])
    c, d = complex(gate[1][0]), complex(gate[1][1])
    out = vector.copy()
    bit = 1 << target
    for base in range(len(vector)):
        if base & bit:
            continue
        partner = base | bit
        x, y = vector[base], vector[partner]
        out[base] = a * x + b * y
        out[partner] = c * x + d * y
    return _validate_state(out, atol=1e-7)


def hadamard(state: Sequence[Complex], target: int) -> list[Complex]:
    s = 1 / math.sqrt(2)
    return apply_single_qubit(state, ((s, s), (s, -s)), target)


def pauli_x(state: Sequence[Complex], target: int) -> list[Complex]:
    return apply_single_qubit(state, ((0, 1), (1, 0)), target)


def cnot(state: Sequence[Complex], control: int, target: int) -> list[Complex]:
    vector = _validate_state(state)
    n = len(vector).bit_length() - 1
    if not (0 <= control < n and 0 <= target < n) or control == target:
        raise ValueError("control and target must be distinct valid qubits")
    out = vector.copy()
    cbit, tbit = 1 << control, 1 << target
    for index in range(len(vector)):
        if index & cbit and not index & tbit:
            partner = index | tbit
            out[index], out[partner] = vector[partner], vector[index]
    return _validate_state(out)


def probabilities(state: Sequence[Complex]) -> list[float]:
    vector = _validate_state(state)
    return [float(abs(z) ** 2) for z in vector]


def measure(state: Sequence[Complex], shots: int = 1, seed: int = 0) -> list[str]:
    """Sample computational-basis outcomes with a reproducible PRNG seed."""
    if not isinstance(shots, int) or shots < 1:
        raise ValueError("shots must be a positive integer")
    p = probabilities(state)
    rng = random.Random(seed)
    outcomes = [format(i, f"0{len(p).bit_length() - 1}b") for i in range(len(p))]
    return rng.choices(outcomes, weights=p, k=shots)
