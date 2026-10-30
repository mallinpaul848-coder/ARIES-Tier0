// PRISE benchmark: compare mathematically equivalent kernels after correctness gates.
// This is a CPU microbenchmark, not end-to-end API or model inference.
#include "aries_harmonic_kernel.hpp"
#include "aries_fast_kernel.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
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

template <typename Reference, typename Candidate>
void compare(const char* label,
             const std::array<std::uint64_t, kInputCount>& inputs,
             Reference reference_fn, Candidate candidate_fn) {
    for (const auto value : inputs) {
        if (reference_fn(value) != candidate_fn(value)) {
            std::cerr << "FAIL: correctness gate failed for " << label << '\\n';
            std::exit(1);
        }
    }

    std::array<double, kRounds> reference{}, candidate{};
    for (std::size_t round = 0; round < kRounds; ++round) {
        if ((round & 1U) == 0) {
            reference[round] = measure_ns_per_op(inputs, reference_fn);
            candidate[round] = measure_ns_per_op(inputs, candidate_fn);
        } else {
            candidate[round] = measure_ns_per_op(inputs, candidate_fn);
            reference[round] = measure_ns_per_op(inputs, reference_fn);
        }
    }

    const double ref_p50 = percentile(reference, 0.50);
    const double candidate_p50 = percentile(candidate, 0.50);
    std::cout << label << "_correctness=PASS inputs=" << kInputCount << '\\n'
              << label << "_reference_p50_ns_op=" << ref_p50 << '\\n'
              << label << "_reference_p95_ns_op=" << percentile(reference, 0.95) << '\\n'
              << label << "_candidate_p50_ns_op=" << candidate_p50 << '\\n'
              << label << "_candidate_p95_ns_op=" << percentile(candidate, 0.95) << '\\n'
              << label << "_candidate_speedup=" << (ref_p50 / candidate_p50) << "x\\n";
}
}

int main() {
    using aries::core::UltraLowLatencyHarmonicEngine;
    const auto inputs = make_inputs();

    compare("digital_root_lookup", inputs,
        [](std::uint64_t n) { return aries::core::compute_digital_root(n); },
        [](std::uint64_t n) { return UltraLowLatencyHarmonicEngine::table_digital_root(n); });

    compare("harmonic_mod3", inputs,
        [](std::uint64_t n) { return aries::core::is_harmonic_node(n); },
        [](std::uint64_t n) { return aries::core::is_harmonic_node_fast(n); });

    std::cout << "rounds=" << kRounds << '\\n'
              << "operations_per_round=" << (kInputCount * kRepeats) << '\\n'
              << "sink=" << sink << '\\n'
              << "scope=isolated CPU kernels; excludes API, model inference, and network\\n";
    return 0;
}
