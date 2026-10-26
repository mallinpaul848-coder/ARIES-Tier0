"""Measured software/hardware co-scheduling primitives for ARIES/MALLIN.

The double helix is an architectural metaphor: two cooperating execution strands
around one workload/telemetry axis. It does not itself bypass physical hardware
limits. Hardware adapters must provide real measurements and explicit capability
metadata; quantum adapters are optional and are never assumed faster by default.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from statistics import median
from typing import Callable, Iterable

@dataclass(frozen=True)
class Candidate:
    name: str
    strand: str  # "software" or "hardware"
    execute: Callable[[object], object]
    measured_latency_ms: float | None = None
    measured_memory_mb: float | None = None
    validated: bool = False
    requires_quantum_device: bool = False

@dataclass(frozen=True)
class Measurement:
    candidate: str
    latency_ms: float
    success: bool
    detail: str = ""

class DoubleHelixScheduler:
    """Select only validated candidates that satisfy a latency budget.

    Candidate measurements are refreshed by `benchmark`; unvalidated candidates
    are not eligible for automatic selection. The default policy is conservative:
    preserve a known-good baseline and fail closed on invalid measurements.
    """
    def __init__(self, latency_budget_ms: float, quantum_available: bool = False):
        if not isfinite(latency_budget_ms) or latency_budget_ms <= 0:
            raise ValueError("latency budget must be positive and finite")
        self.latency_budget_ms = latency_budget_ms
        self.quantum_available = quantum_available
        self.candidates: dict[str, Candidate] = {}
        self.history: dict[str, list[Measurement]] = {}

    def register(self, candidate: Candidate) -> None:
        if not candidate.name or candidate.strand not in {"software", "hardware"}:
            raise ValueError("candidate needs a name and valid strand")
        if candidate.name in self.candidates:
            raise ValueError("duplicate candidate name")
        if candidate.requires_quantum_device and not self.quantum_available:
            # Keep metadata, but it remains ineligible until a device is configured.
            self.candidates[candidate.name] = candidate
            self.history[candidate.name] = []
            return
        self.candidates[candidate.name] = candidate
        self.history[candidate.name] = []

    def benchmark(self, name: str, workload: object, repetitions: int = 5) -> Measurement:
        if repetitions < 3:
            raise ValueError("use at least three repetitions")
        candidate = self.candidates[name]
        if candidate.requires_quantum_device and not self.quantum_available:
            raise RuntimeError("candidate requires an available quantum device adapter")
        samples: list[float] = []
        output = None
        for _ in range(repetitions):
            import time
            start = time.perf_counter()
            output = candidate.execute(workload)
            elapsed = (time.perf_counter() - start) * 1000.0
            if not isfinite(elapsed) or elapsed < 0:
                raise ValueError("invalid timing sample")
            samples.append(elapsed)
        score = float(median(samples))
        result = Measurement(name, score, True, f"{repetitions} repeated local measurements; output type {type(output).__name__}")
        self.history[name].append(result)
        return result

    def choose(self, baseline_name: str) -> Candidate:
        if baseline_name not in self.candidates:
            raise KeyError("baseline candidate is not registered")
        baseline = self.candidates[baseline_name]
        baseline_history = self.history[baseline_name]
        if not baseline.validated or not baseline_history:
            raise RuntimeError("baseline must be validated and benchmarked first")
        eligible: list[tuple[float, Candidate]] = [(median([m.latency_ms for m in baseline_history]), baseline)]
        for name, candidate in self.candidates.items():
            if name == baseline_name or not candidate.validated:
                continue
            if candidate.requires_quantum_device and not self.quantum_available:
                continue
            history = self.history[name]
            if not history:
                continue
            score = float(median([m.latency_ms for m in history]))
            if score <= self.latency_budget_ms and score < eligible[0][0]:
                eligible.append((score, candidate))
        eligible.sort(key=lambda pair: pair[0])
        return eligible[0][1]

    def report(self) -> dict[str, object]:
        return {
            "latency_budget_ms": self.latency_budget_ms,
            "quantum_available": self.quantum_available,
            "candidates": {name: {
                "strand": c.strand, "validated": c.validated,
                "requires_quantum_device": c.requires_quantum_device,
                "samples": len(self.history[name]),
                "median_latency_ms": float(median([m.latency_ms for m in self.history[name]])) if self.history[name] else None,
            } for name, c in self.candidates.items()},
            "policy": "only measured, validated candidates; retain baseline on uncertainty",
        }