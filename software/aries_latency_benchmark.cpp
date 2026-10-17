// ARIES latency benchmark harness
// Measures a small deterministic integer kernel in batches to reduce timer overhead.
// IMPORTANT: this is a CPU microbenchmark, NOT a measurement of full AI inference
// and cannot by itself establish sub-nanosecond end-to-end latency.

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
#include <atomic>

#if defined(_WIN32)
  #define NOMINMAX
  #include <windows.h>
#elif defined(__linux__)
  #include <pthread.h>
  #include <sched.h>
#endif

namespace {
using Clock = std::chrono::steady_clock;
constexpr std::uint64_t kIterations = 1'000'000;
constexpr std::uint64_t kBatchSize = 1'000;
volatile std::uint64_t g_sink = 0;

bool pin_to_cpu_zero() {
#if defined(_WIN32)
    return SetThreadAffinityMask(GetCurrentThread(), 1) != 0;
#elif defined(__linux__)
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(0, &cpuset);
    return pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset) == 0;
#else
    return false;
#endif
}

// A real, deterministic integer workload; unlike an empty inline-assembly
// function, this performs operations whose result is consumed after timing.
inline std::uint64_t execute_aries_kernel(std::uint64_t x) {
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    return x * 0x2545F4914F6CDD1DULL;
}

double percentile(const std::vector<double>& sorted, double p) {
    if (sorted.empty()) return 0.0;
    const auto index = static_cast<std::size_t>(p * static_cast<double>(sorted.size() - 1));
    return sorted[index];
}

void report(const char* name, double value) {
    std::cout << std::left << std::setw(18) << name
              << std::right << std::fixed << std::setprecision(3)
              << value << " ns/op\n";
}
}

int main(int argc, char** argv) {
    std::uint64_t iterations = kIterations;
    if (argc > 1) {
        try {
            const auto parsed = std::stoull(argv[1]);
            if (parsed < kBatchSize || parsed > 100'000'000ULL) {
                std::cerr << "Iterations must be between 1000 and 100000000.\n";
                return 2;
            }
            iterations = (parsed / kBatchSize) * kBatchSize;
        } catch (...) {
            std::cerr << "Usage: aries_latency_benchmark [iterations]\n";
            return 2;
        }
    }

    const bool pinned = pin_to_cpu_zero();
    std::uint64_t state = 0xA71E5ULL;
    for (std::uint64_t i = 0; i < 20'000; ++i) state = execute_aries_kernel(state + i);
    g_sink = state;

    std::vector<double> samples;
    samples.reserve(static_cast<std::size_t>(iterations / kBatchSize));
    const auto total_start = Clock::now();

    for (std::uint64_t base = 0; base < iterations; base += kBatchSize) {
        const auto start = Clock::now();
        for (std::uint64_t j = 0; j < kBatchSize; ++j) {
            state = execute_aries_kernel(state + base + j);
        }
        std::atomic_signal_fence(std::memory_order_seq_cst);
        const auto end = Clock::now();
        const double elapsed_ns =
            std::chrono::duration<double, std::nano>(end - start).count();
        samples.push_back(elapsed_ns / static_cast<double>(kBatchSize));
    }

    const auto total_end = Clock::now();
    g_sink = state;
    std::sort(samples.begin(), samples.end());
    const double total_ns = std::chrono::duration<double, std::nano>(total_end - total_start).count();

    std::cout << "==================================================\n"
              << "          ARIES CPU LATENCY BENCHMARK             \n"
              << "==================================================\n"
              << "Kernel: deterministic 64-bit integer mixing\n"
              << "Iterations: " << iterations << "\n"
              << "Batch size: " << kBatchSize << "\n"
              << "CPU affinity core 0: " << (pinned ? "set" : "not available; best effort") << "\n"
              << "Clock: std::chrono::steady_clock\n"
              << "--------------------------------------------------\n";
    report("Min", samples.front());
    report("P50", percentile(samples, 0.50));
    report("P99", percentile(samples, 0.99));
    report("P99.9", percentile(samples, 0.999));
    report("Max", samples.back());
    report("Overall average", total_ns / static_cast<double>(iterations));
    std::cout << "Total elapsed: " << std::fixed << std::setprecision(3)
              << total_ns / 1'000'000.0 << " ms\n"
              << "Result checksum: " << g_sink << "\n"
              << "NOTE: ns/op is batch-average CPU kernel timing. It excludes AI inference,\n"
              << "network, model loading, and user-visible response latency. Timer and OS\n"
              << "overhead remain; these figures do not prove sub-nanosecond execution.\n"
              << "==================================================\n";
    return 0;
}
