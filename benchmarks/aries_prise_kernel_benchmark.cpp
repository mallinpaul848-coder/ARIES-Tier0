// Reproducible PRISE digital-root kernel comparison.
// Measures reference modulo implementation vs the table-based candidate.
// This is a CPU microbenchmark, not language-model inference.
#include "aries_harmonic_kernel.hpp"
#include "aries_fast_kernel.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <numeric>

namespace {
constexpr std::size_t kInputCount = 4096;
constexpr std::size_t kRounds = 11;
constexpr std::size_t kRepeats = 256;
volatile std::uint64_t sink = 0;

std::array<std::uint64_t, kInputCount> make_inputs() {
    std::array<std::uint64_t, kInputCount> values{};
    std::uint64_t x = 0x9E3779B97F4A7C15ULL;
    for (auto& value : values) {
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        value = x * 0x2545F4914F6CDD1DULL;
    }
    return values;
}

template <typename Function>
double measure_ns_per_op(const std::array<std::uint64_t, kInputCount>& inputs,
                         Function function) {
    const auto start = std::chrono::steady_clock::now();
    std::uint64_t local = 0;
    for (std::size_t repeat = 0; repeat < kRepeats; ++repeat) {
        for (const auto value : inputs) local += function(value);
    }
    const auto stop = std::chrono::steady_clock::now();
    sink = sink ^ local;
    const auto elapsed = std::chrono::duration<double, std::nano>(stop - start).count();
    return elapsed / static_cast<double>(kInputCount * kRepeats);
}

double percentile(std::array<double, kRounds> values, double p) {
    std::sort(values.begin(), values.end());
    const auto index = static_cast<std::size_t>(p * (values.size() - 1));
    return values[index];
}
}

int main() {
    using aries::core::compute_digital_root;
    using aries::core::UltraLowLatencyHarmonicEngine;
    const auto inputs = make_inputs();

    // Correctness gate before timing: reject any candidate mismatch.
    for (const auto value : inputs) {
        if (compute_digital_root(value) !=
            UltraLowLatencyHarmonicEngine::fast_digital_root(value)) {
            std::cerr << "FAIL: candidate differs from reference\n";
            return 1;
        }
    }

    std::array<double, kRounds> reference{}, candidate{};
    for (std::size_t round = 0; round < kRounds; ++round) {
        // Alternate order to reduce systematic warm-up/order bias.
        if ((round & 1U) == 0) {
            reference[round] = measure_ns_per_op(inputs, compute_digital_root);
            candidate[round] = measure_ns_per_op(
                inputs, UltraLowLatencyHarmonicEngine::fast_digital_root);
        } else {
            candidate[round] = measure_ns_per_op(
                inputs, UltraLowLatencyHarmonicEngine::fast_digital_root);
            reference[round] = measure_ns_per_op(inputs, compute_digital_root);
        }
    }

    const double ref_median = percentile(reference, 0.50);
    const double fast_median = percentile(candidate, 0.50);
    std::cout << "benchmark=prise_digital_root_comparison\n"
              << "correctness=PASS (" << kInputCount << " inputs)\n"
              << "rounds=" << kRounds << "\n"
              << "operations_per_round=" << (kInputCount * kRepeats) << "\n"
              << "reference_modulo_p50_ns_op=" << ref_median << "\n"
              << "reference_modulo_p95_ns_op=" << percentile(reference, 0.95) << "\n"
              << "table_candidate_p50_ns_op=" << fast_median << "\n"
              << "table_candidate_p95_ns_op=" << percentile(candidate, 0.95) << "\n"
              << "candidate_speedup=" << (ref_median / fast_median) << "x\n"
              << "sink=" << sink << "\n"
              << "limitation=CPU kernel only; excludes API, model inference, and network\n";
    return 0;
}
