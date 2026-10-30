"""Tests against actual ARIES deterministic code, not placeholder identity functions."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from aries_math.positive_impact import ImpactInputs, score_positive_impact


ROOT = Path(__file__).resolve().parents[1]


class DeterministicCoreTests(unittest.TestCase):
    def test_prise_scoring_is_repeatable_for_identical_inputs(self):
        inputs = ImpactInputs(
            priority=0.8, benefit=0.9, risk=0.2,
            systemic_effect=0.7, emergence=0.4,
            confidence=0.95, reversibility=0.8,
        )
        first = score_positive_impact(inputs)
        for _ in range(1000):
            self.assertEqual(score_positive_impact(inputs), first)

    def test_independent_parallel_prise_calls_match_serial_reference(self):
        cases = [
            ImpactInputs(
                priority=(i % 10) / 10,
                benefit=((i * 3) % 10) / 10,
                risk=((i * 7) % 10) / 10,
                systemic_effect=((i * 5) % 10) / 10,
                emergence=((i * 9) % 10) / 10,
                confidence=0.9,
                reversibility=0.6,
            )
            for i in range(1000)
        ]
        expected = [score_positive_impact(item) for item in cases]
        with ThreadPoolExecutor(max_workers=8) as pool:
            actual = list(pool.map(score_positive_impact, cases))
        self.assertEqual(actual, expected)

    def test_cpp_spsc_engine_is_repeatable_and_zero_heap_allocation_in_steady_state(self):
        compiler = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("No C++ compiler found; C++ core verification requires c++/g++/clang++.")
        source = r"""
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <new>
#include "include/aries_tier0_engine.hpp"

static std::size_t allocation_count = 0;
static bool track_allocations = false;

void* operator new(std::size_t size) {
    if (track_allocations) ++allocation_count;
    if (void* p = std::malloc(size ? size : 1)) return p;
    throw std::bad_alloc();
}
void* operator new[](std::size_t size) {
    if (track_allocations) ++allocation_count;
    if (void* p = std::malloc(size ? size : 1)) return p;
    throw std::bad_alloc();
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete[](void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
void operator delete[](void* p, std::size_t) noexcept { std::free(p); }

static bool run_sequence(std::uint64_t* observed, std::size_t count) {
    aries::core::AriesDeterministicEngine<1024> engine;
    for (std::size_t i = 0; i < count; ++i) {
        const std::uint64_t value = static_cast<std::uint64_t>(i * 17 + 3);
        if (!engine.push(value)) return false;
        std::uint64_t payload = 0, score = 0;
        bool harmonic = false;
        if (!engine.pop(payload, score, harmonic)) return false;
        if (payload != value) return false;
        const std::uint64_t root = value % 9 == 0 ? 9 : value % 9;
        if (score != value * root) return false;
        if (harmonic != (value % 3 == 0)) return false;
        observed[i] = payload ^ score ^ static_cast<std::uint64_t>(harmonic);
    }
    return true;
}

int main() {
    constexpr std::size_t count = 1000;
    std::uint64_t first[count]{};
    std::uint64_t second[count]{};
    track_allocations = true;
    const bool first_ok = run_sequence(first, count);
    const bool second_ok = run_sequence(second, count);
    track_allocations = false;
    if (!first_ok || !second_ok) return 2;
    for (std::size_t i = 0; i < count; ++i)
        if (first[i] != second[i]) return 3;
    if (allocation_count != 0) return 4;
    std::printf("PASS deterministic=%zu steady_state_heap_allocations=%zu\n",
                count * 2, allocation_count);
    return 0;
}
"""
        with tempfile.TemporaryDirectory(prefix="aries-core-test-") as temp:
            temp_path = Path(temp)
            source_path = temp_path / "deterministic_core_test.cpp"
            binary_path = temp_path / "deterministic_core_test"
            source_path.write_text(source, encoding="utf-8")
            compile_result = subprocess.run(
                [compiler, "-std=c++17", "-O2", "-pthread", "-I", str(ROOT),
                 str(source_path), "-o", str(binary_path)],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(
                compile_result.returncode, 0,
                "C++ core test compilation failed:\n" + compile_result.stdout + compile_result.stderr,
            )
            execution = subprocess.run(
                [str(binary_path)], capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(
                execution.returncode, 0,
                "C++ core test failed:\n" + execution.stdout + execution.stderr,
            )
            self.assertIn("steady_state_heap_allocations=0", execution.stdout)


if __name__ == "__main__":
    unittest.main()
