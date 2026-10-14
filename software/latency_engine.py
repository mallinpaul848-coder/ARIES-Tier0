"""Measured low-latency routing utilities for ARIES.

The fast path caches only the deterministic rule-engine result. Unknown prompts still
fall through to the native n-gram generator. Timings are observed with
time.perf_counter_ns(); the unit is nanoseconds, but the clock's resolution and
runtime overhead mean this does not imply sub-nanosecond execution.
"""
from __future__ import annotations

from collections import OrderedDict, deque
from math import ceil
import threading
import time
from typing import Callable, Any


def normalize_prompt(prompt: str) -> str:
    """Normalize whitespace only; preserve case so exact-output answers remain safe."""
    return " ".join(str(prompt).strip().split())


class FastPathEngine:
    """Thread-safe, bounded LRU memoization for deterministic narrow tasks."""

    def __init__(self, solver: Callable[[str], Any], max_entries: int = 1024):
        if isinstance(max_entries, bool) or not isinstance(max_entries, int) or max_entries < 0:
            raise ValueError("max_entries must be a non-negative integer")
        self._solver = solver
        self.max_entries = max_entries
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.RLock()
        self._calls = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._solver_calls = 0
        self._evictions = 0

    def solve_with_metadata(self, prompt: str) -> tuple[Any, bool, int]:
        """Return (solver_result, cache_hit, elapsed_ns); None remains a valid cached result."""
        started_ns = time.perf_counter_ns()
        key = normalize_prompt(prompt)
        with self._lock:
            self._calls += 1
            if self.max_entries and key in self._cache:
                result = self._cache[key]
                self._cache.move_to_end(key)
                self._cache_hits += 1
                return result, True, max(0, time.perf_counter_ns() - started_ns)
            self._cache_misses += 1

        # Run outside the lock so unrelated prompts can be processed concurrently.
        result = self._solver(key)
        with self._lock:
            self._solver_calls += 1
            if self.max_entries:
                self._cache[key] = result
                self._cache.move_to_end(key)
                while len(self._cache) > self.max_entries:
                    self._cache.popitem(last=False)
                    self._evictions += 1
        return result, False, max(0, time.perf_counter_ns() - started_ns)

    def solve(self, prompt: str) -> Any:
        """Simple compatibility wrapper for callers that only need the result."""
        result, _cache_hit, _elapsed_ns = self.solve_with_metadata(prompt)
        return result

    def clear(self, reset_counters: bool = False) -> None:
        with self._lock:
            self._cache.clear()
            if reset_counters:
                self._calls = self._cache_hits = self._cache_misses = 0
                self._solver_calls = self._evictions = 0

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "cache_enabled": self.max_entries > 0,
                "max_entries": self.max_entries,
                "entries": len(self._cache),
                "calls": self._calls,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "solver_calls": self._solver_calls,
                "evictions": self._evictions,
                "hit_rate_percent": round(100 * self._cache_hits / self._calls, 3) if self._calls else 0.0,
            }


class LatencyMonitor:
    """Bounded per-operation latency samples with percentile summaries."""

    def __init__(self, window_size: int = 2048):
        if isinstance(window_size, bool) or not isinstance(window_size, int) or window_size < 1:
            raise ValueError("window_size must be a positive integer")
        self.window_size = window_size
        self._samples: dict[str, deque[int]] = {}
        self._lock = threading.RLock()

    def record(self, operation: str, duration_ns: int) -> None:
        if not isinstance(operation, str) or not operation.strip():
            raise ValueError("operation must be a non-empty string")
        if isinstance(duration_ns, bool) or not isinstance(duration_ns, int) or duration_ns < 0:
            raise ValueError("duration_ns must be a non-negative integer")
        with self._lock:
            if operation not in self._samples:
                self._samples[operation] = deque(maxlen=self.window_size)
            self._samples[operation].append(duration_ns)

    @staticmethod
    def _percentile(sorted_samples: list[int], percentile: float) -> int:
        if not sorted_samples:
            return 0
        index = max(0, ceil(percentile * len(sorted_samples)) - 1)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            route_samples = {name: list(values) for name, values in self._samples.items()}
        routes = {}
        for name, values in route_samples.items():
            ordered = sorted(values)
            n = len(ordered)
            routes[name] = {
                "sample_count": n,
                "min_ns": ordered[0] if n else 0,
                "median_ns": self._percentile(ordered, 0.50),
                "p95_ns": self._percentile(ordered, 0.95),
                "p99_ns": self._percentile(ordered, 0.99),
                "max_ns": ordered[-1] if n else 0,
                "window_size": self.window_size,
            }
        clock = time.get_clock_info("perf_counter")
        return {
            "unit": "nanoseconds",
            "clock": {
                "name": "perf_counter",
                "implementation": clock.implementation,
                "nominal_resolution_ns": max(1, round(clock.resolution * 1_000_000_000)),
                "monotonic": clock.monotonic,
                "adjustable": clock.adjustable,
            },
            "measurements": routes,
            "interpretation": (
                "Server-side elapsed-time samples only. Timer units are nanoseconds; "
                "this does not establish sub-nanosecond runtime or CPU-cycle latency."
            ),
            "sub_nanosecond_latency_verified": False,
        }
