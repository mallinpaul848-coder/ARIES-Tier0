"""Universal ARIES/MALLIN component orchestrator with latency telemetry.

This module links independently testable components through explicit adapters.
It does not assume any proprietary mathematical formula is correct or faster.
Components are opt-in and only become production routes after measured validation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from time import perf_counter
from typing import Any, Callable, Mapping, Sequence


Component = Callable[[Any], Any]


@dataclass
class StageMetric:
    name: str
    calls: int = 0
    failures: int = 0
    total_ms: float = 0.0
    samples_ms: list[float] = field(default_factory=list)

    @property
    def mean_ms(self) -> float:
        return mean(self.samples_ms) if self.samples_ms else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.samples_ms:
            return 0.0
        ordered = sorted(self.samples_ms)
        pos = (len(ordered) - 1) * 0.95
        lo = int(pos)
        hi = min(lo + 1, len(ordered) - 1)
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


class UniversalPerformanceOrchestrator:
    """Run registered stages in order and measure each stage and total latency.

    A stage receives the current value and returns the next value. Register
    existing ARIES, MALLIN, PRISE, learning, quantum-simulation, cache, or model
    adapters only after they have independent tests. A failing optional stage
    may be configured as non-fatal; its input is preserved as a safe fallback.
    """

    def __init__(self) -> None:
        self._stages: list[tuple[str, Component, bool]] = []
        self.metrics: dict[str, StageMetric] = {}
        self.total_samples_ms: list[float] = []

    def register(self, name: str, component: Component, *, optional: bool = False) -> None:
        if not name or not callable(component):
            raise ValueError("stage needs a non-empty name and callable component")
        if any(existing == name for existing, _, _ in self._stages):
            raise ValueError(f"duplicate stage name: {name}")
        self._stages.append((name, component, optional))
        self.metrics[name] = StageMetric(name)

    def run(self, value: Any) -> Any:
        total_start = perf_counter()
        current = value
        try:
            for name, component, optional in self._stages:
                metric = self.metrics[name]
                start = perf_counter()
                try:
                    result = component(current)
                    current = result
                except Exception:
                    metric.failures += 1
                    if not optional:
                        raise
                finally:
                    elapsed = (perf_counter() - start) * 1000.0
                    metric.calls += 1
                    metric.total_ms += elapsed
                    metric.samples_ms.append(elapsed)
            return current
        finally:
            self.total_samples_ms.append((perf_counter() - total_start) * 1000.0)

    def report(self) -> dict[str, Any]:
        def pct(values: Sequence[float], p: float) -> float:
            if not values:
                return 0.0
            ordered = sorted(values)
            pos = (len(ordered) - 1) * p
            lo = int(pos)
            hi = min(lo + 1, len(ordered) - 1)
            return round(ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo), 3)

        return {
            "scope": "local component pipeline; not an external certification",
            "total_calls": len(self.total_samples_ms),
            "total_mean_ms": round(mean(self.total_samples_ms), 3) if self.total_samples_ms else 0.0,
            "total_p50_ms": pct(self.total_samples_ms, 0.50),
            "total_p95_ms": pct(self.total_samples_ms, 0.95),
            "stages": {
                name: {
                    "calls": m.calls,
                    "failures": m.failures,
                    "mean_ms": round(m.mean_ms, 3),
                    "p95_ms": round(m.p95_ms, 3),
                }
                for name, m in self.metrics.items()
            },
        }
