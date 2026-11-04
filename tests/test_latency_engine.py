import time

import pytest

from software.latency_engine import FastPathEngine, LatencyMonitor, normalize_prompt


def test_normalize_prompt_preserves_case():
    assert normalize_prompt("  Reply   EXACTLY:   ABC  ") == "Reply EXACTLY: ABC"
    assert normalize_prompt("ABC") != normalize_prompt("abc")


def test_fast_path_caches_deterministic_answer():
    calls = []
    def solver(prompt):
        calls.append(prompt)
        return prompt.upper()

    engine = FastPathEngine(solver, max_entries=2)
    first = engine.solve_with_metadata(" hello   there ")
    second = engine.solve_with_metadata("hello there")
    assert first[0] == second[0] == "HELLO THERE"
    assert first[1] is False
    assert second[1] is True
    assert len(calls) == 1
    assert engine.snapshot()["cache_hits"] == 1


def test_none_results_are_cached():
    calls = []
    engine = FastPathEngine(lambda prompt: calls.append(prompt), max_entries=5)
    assert engine.solve_with_metadata("unknown")[0] is None
    assert engine.solve_with_metadata("unknown")[0] is None
    assert len(calls) == 1


def test_lru_eviction_is_bounded():
    engine = FastPathEngine(lambda prompt: prompt, max_entries=2)
    engine.solve("a")
    engine.solve("b")
    engine.solve("a")  # refresh a
    engine.solve("c")  # evict b
    assert engine.snapshot()["entries"] == 2
    assert engine.snapshot()["evictions"] == 1
    assert engine.solve_with_metadata("a")[1] is True
    assert engine.solve_with_metadata("b")[1] is False


def test_cache_can_be_disabled():
    calls = []
    engine = FastPathEngine(lambda prompt: calls.append(prompt) or prompt, max_entries=0)
    engine.solve("x")
    engine.solve("x")
    assert len(calls) == 2
    assert engine.snapshot()["cache_enabled"] is False


def test_invalid_capacity():
    with pytest.raises(ValueError):
        FastPathEngine(lambda prompt: prompt, max_entries=-1)


def test_latency_monitor_percentiles_and_bounded_window():
    monitor = LatencyMonitor(window_size=4)
    for sample in [10, 20, 30, 40, 50]:
        monitor.record("chat", sample)
    report = monitor.snapshot()
    chat = report["measurements"]["chat"]
    assert chat["sample_count"] == 4
    assert chat["min_ns"] == 20
    assert chat["median_ns"] == 30
    assert chat["p95_ns"] == 50
    assert chat["max_ns"] == 50
    assert report["sub_nanosecond_latency_verified"] is False
    assert report["clock"]["nominal_resolution_ns"] >= 1


def test_latency_monitor_rejects_invalid_samples():
    monitor = LatencyMonitor()
    with pytest.raises(ValueError):
        monitor.record("chat", -1)
    with pytest.raises(ValueError):
        monitor.record("", 1)


def test_deterministic_routes_run_before_generative_fallback():
    from software.latency_engine import resolve_deterministic_routes

    calls = []
    engine = FastPathEngine(lambda prompt: calls.append("fast") or "cached calculation", max_entries=4)
    def known(prompt):
        calls.append("known")
        return None
    def math_router(prompt):
        calls.append("math")
        return {"route": "math_test", "answer": "math result"}

    result = resolve_deterministic_routes("17 * 19", known, engine, math_router)
    assert result[0] == "cached calculation"
    assert result[4] == "deterministic_fast_path"
    assert calls == ["known", "fast"]


def test_math_route_runs_after_fast_path_miss_and_before_model():
    from software.latency_engine import resolve_deterministic_routes

    calls = []
    engine = FastPathEngine(lambda prompt: calls.append("fast") or None, max_entries=4)
    def known(prompt):
        calls.append("known")
        return None
    def math_router(prompt):
        calls.append("math")
        return {"route": "phase8_vector", "answer": "math result"}

    result = resolve_deterministic_routes("phase 8 1,2", known, engine, math_router)
    assert result[0] == "math result"
    assert result[3] == "phase8_vector"
    assert result[4] == "math_router"
    assert calls == ["known", "fast", "math"]


def test_unknown_prompt_is_left_for_generative_fallback():
    from software.latency_engine import resolve_deterministic_routes

    engine = FastPathEngine(lambda prompt: None, max_entries=4)
    result = resolve_deterministic_routes("tell me a story", lambda _p: None, engine, lambda _p: None)
    assert result[0] is None
    assert result[4] == "generative_fallback"
