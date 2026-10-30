"""Bounded classical state-vector simulator for ARIES quantum experiments.

This simulates small quantum circuits on a classical CPU. It does not use
quantum hardware and does not claim quantum speedup. Keep it off the chat hot path.
"""
from __future__ import annotations
import cmath
import math
import random

MAX_QUBITS = 12

def digital_root(value: int) -> int:
    """Conventional digital root for an integer."""
    n = abs(int(value))
    return 0 if n == 0 else 1 + (n - 1) % 9

def harmonic_phase(value: int) -> float:
    """Encode the digital root as a phase on the unit circle."""
    return 2.0 * math.pi * digital_root(value) / 9.0

class HarmonicStateVector:
    def __init__(self, qubits: int):
        if isinstance(qubits, bool) or not isinstance(qubits, int) or not 1 <= qubits <= MAX_QUBITS:
            raise ValueError(f"qubits must be an integer from 1 through {MAX_QUBITS}")
        self.qubits = qubits
        self.amplitudes = [0j] * (1 << qubits)
        self.amplitudes[0] = 1 + 0j

    def _check(self, q: int) -> None:
        if isinstance(q, bool) or not isinstance(q, int) or not 0 <= q < self.qubits:
            raise ValueError("qubit index out of range")

    def hadamard(self, q: int):
        self._check(q)
        stride = 1 << q
        scale = 1.0 / math.sqrt(2.0)
        for base in range(0, len(self.amplitudes), stride << 1):
            for offset in range(stride):
                i, j = base + offset, base + offset + stride
                a, b = self.amplitudes[i], self.amplitudes[j]
                self.amplitudes[i], self.amplitudes[j] = (a + b) * scale, (a - b) * scale
        return self

    def phase(self, q: int, angle: float):
        self._check(q)
        factor = cmath.exp(1j * float(angle))
        mask = 1 << q
        for i in range(len(self.amplitudes)):
            if i & mask:
                self.amplitudes[i] *= factor
        return self

    def harmonic_phase(self, q: int, value: int):
        return self.phase(q, harmonic_phase(value))

    def cnot(self, control: int, target: int):
        self._check(control)
        self._check(target)
        if control == target:
            raise ValueError("control and target must differ")
        cmask, tmask = 1 << control, 1 << target
        for i in range(len(self.amplitudes)):
            if i & cmask and not i & tmask:
                j = i | tmask
                self.amplitudes[i], self.amplitudes[j] = self.amplitudes[j], self.amplitudes[i]
        return self

    def probabilities(self) -> list[float]:
        return [float((a.conjugate() * a).real) for a in self.amplitudes]

    def norm_squared(self) -> float:
        return sum(self.probabilities())

    def measure(self, shots: int = 1, seed: int = 0) -> dict[str, int]:
        if isinstance(shots, bool) or not isinstance(shots, int) or shots < 1:
            raise ValueError("shots must be a positive integer")
        probs = self.probabilities()
        if abs(sum(probs) - 1.0) > 1e-9:
            raise ArithmeticError("state vector is not normalized")
        rng = random.Random(seed)
        outcomes = [format(i, f"0{self.qubits}b")[::-1] for i in range(len(probs))]
        counts: dict[str, int] = {}
        for _ in range(shots):
            draw, cumulative, selected = rng.random(), 0.0, len(probs) - 1
            for i, probability in enumerate(probs):
                cumulative += probability
                if draw < cumulative:
                    selected = i
                    break
            bitstring = outcomes[selected]
            counts[bitstring] = counts.get(bitstring, 0) + 1
        return dict(sorted(counts.items()))

    def snapshot(self) -> dict:
        return {"qubits": self.qubits, "states": len(self.amplitudes),
                "norm_squared": self.norm_squared(),
                "execution": "classical_state_vector_simulation",
                "quantum_hardware_used": False}
