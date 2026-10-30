// PRISE benchmark: compare mathematically equivalent kernels after correctness gates.
// This is a CPU microbenchmark, not end-to-end API or model inference.
#include "aries_harmonic_kernel.hpp"
#include "aries_fast_kernel.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>

namespace {
constexpr std::size_t kInputCount = 4096;
constexpr std::size_t kRounds = 15;
constexpr std::size_t kRepeats = 128;
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
        for (const auto value : inputs) local += static_cast<std::uint64_t>(function(value));
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

} // namespace

int main() {
    using aries::core::compute_digital_root;
    using aries::core::UltraLowLatencyHarmonicEngine;
    const auto inputs = make_inputs();

    // Correctness gate before timing: reject any candidate mismatch.
    for (const auto value : inputs) {
        if (compute_digital_root(value) !=
            UltraLowLatencyHarmonicEngine::table_digital_root(value)) {
            std::cerr << "FAIL: table candidate differs from reference\n";
            return 1;
        }
    }

    // Warm both paths before collecting samples.
    (void)measure_ns_per_op(inputs, compute_digital_root);
    (void)measure_ns_per_op(inputs, UltraLowLatencyHarmonicEngine::table_digital_root);

    std::array<double, kRounds> reference{}, candidate{};
    for (std::size_t round = 0; round < kRounds; ++round) {
        // Both branches compare the same two implementations. Alternate order
        // to reduce systematic cache, thermal, and scheduling bias.
        if ((round & 1U) == 0) {
            reference[round] = measure_ns_per_op(inputs, compute_digital_root);
            candidate[round] = measure_ns_per_op(
                inputs, UltraLowLatencyHarmonicEngine::table_digital_root);
        } else {
            candidate[round] = measure_ns_per_op(
                inputs, UltraLowLatencyHarmonicEngine::table_digital_root);
            reference[round] = measure_ns_per_op(inputs, compute_digital_root);
        }
    }

    const double ref_median = percentile(reference, 0.50);
    const double candidate_median = percentile(candidate, 0.50);
    const double speedup = ref_median / candidate_median;
    // Compare the cheap mod-3 predicate with full digital-root classification.
    // Both must agree for every input before any timing is accepted.
    std::array<double, kRounds> predicate_reference{}, predicate_candidate{};
    const auto reference_predicate = [](std::uint64_t value) {
        return aries::core::is_harmonic_node(value);
    };
    const auto fast_predicate = [](std::uint64_t value) {
        return aries::core::is_harmonic_node_fast(value);
    };
    for (const auto value : inputs) {
        if (reference_predicate(value) != fast_predicate(value)) {
            std::cerr << "FAIL: mod-3 predicate differs from digital-root reference\\n";
            return 1;
        }
    }
    (void)measure_ns_per_op(inputs, reference_predicate);
    (void)measure_ns_per_op(inputs, fast_predicate);
    for (std::size_t round = 0; round < kRounds; ++round) {
        if ((round & 1U) == 0) {
            predicate_reference[round] = measure_ns_per_op(inputs, reference_predicate);
            predicate_candidate[round] = measure_ns_per_op(inputs, fast_predicate);
        } else {
            predicate_candidate[round] = measure_ns_per_op(inputs, fast_predicate);
            predicate_reference[round] = measure_ns_per_op(inputs, reference_predicate);
        }
    }
    const double predicate_reference_median = percentile(predicate_reference, 0.50);
    const double predicate_candidate_median = percentile(predicate_candidate, 0.50);
    const double predicate_speedup = predicate_reference_median / predicate_candidate_median;

    std::cout << "benchmark=prise_digital_root_comparison\n"
              << "correctness=PASS (" << kInputCount << " inputs)\n"
              << "rounds=" << kRounds << "\n"
              << "operations_per_round=" << (kInputCount * kRepeats) << "\n"
              << "reference_modulo_p50_ns_op=" << ref_median << "\n"
              << "reference_modulo_p95_ns_op=" << percentile(reference, 0.95) << "\n"
              << "table_candidate_p50_ns_op=" << candidate_median << "\n"
              << "table_candidate_p95_ns_op=" << percentile(candidate, 0.95) << "\n"
              << "table_candidate_speedup=" << speedup << "x\n"
              << "candidate_faster_by_median=" << (speedup > 1.0 ? "true" : "false") << "\n"
              << "predicate_correctness=PASS (" << kInputCount << " inputs)\\n"
              << "predicate_reference_digital_root_p50_ns_op=" << predicate_reference_median << "\\n"
              << "predicate_reference_digital_root_p95_ns_op=" << percentile(predicate_reference, 0.95) << "\\n"
              << "predicate_fast_mod3_p50_ns_op=" << predicate_candidate_median << "\\n"
              << "predicate_fast_mod3_p95_ns_op=" << percentile(predicate_candidate, 0.95) << "\\n"
              << "predicate_fast_mod3_speedup=" << predicate_speedup << "x\\n"
              << "predicate_faster_by_median=" << (predicate_speedup > 1.0 ? "true" : "false") << "\\n"
              << "sink=" << sink << "\n"
              << "limitation=CPU kernel only; excludes API, model inference, and network\n";
    return 0;
}
