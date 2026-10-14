#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <string>
#include <thread>
#include <vector>

#if !defined(__linux__) || !defined(__x86_64__)
#error "This benchmark currently requires Linux on x86_64 (TSC + pthread affinity)."
#endif

#include <immintrin.h>
#include <pthread.h>
#include <sched.h>
#include <unistd.h>

struct alignas(64) ARIESOperation {
    uint64_t state_mask = 0xA5A5A5A55A5A5A5AULL;
    uint64_t key = 0x0123456789ABCDEFULL;

    __attribute__((always_inline)) inline uint64_t evaluate() const {
        return (state_mask ^ key) + (state_mask >> 3);
    }
};

static bool pin_to_first_allowed_cpu(int& pinned_cpu) {
    cpu_set_t allowed;
    CPU_ZERO(&allowed);
    if (sched_getaffinity(0, sizeof(allowed), &allowed) != 0) return false;
    for (int cpu = 0; cpu < CPU_SETSIZE; ++cpu) {
        if (CPU_ISSET(cpu, &allowed)) {
            cpu_set_t one;
            CPU_ZERO(&one);
            CPU_SET(cpu, &one);
            if (pthread_setaffinity_np(pthread_self(), sizeof(one), &one) == 0) {
                pinned_cpu = cpu;
                return true;
            }
            return false;
        }
    }
    return false;
}

static inline uint64_t serialized_tsc() {
    _mm_lfence();
    const uint64_t t = __rdtsc();
    _mm_lfence();
    return t;
}

static double calibrate_tsc_ghz() {
    using clock = std::chrono::steady_clock;
    const auto wall0 = clock::now();
    const uint64_t tsc0 = serialized_tsc();
    std::this_thread::sleep_for(std::chrono::milliseconds(250));
    const uint64_t tsc1 = serialized_tsc();
    const auto wall1 = clock::now();
    const double ns = std::chrono::duration<double, std::nano>(wall1 - wall0).count();
    return ns > 0 ? static_cast<double>(tsc1 - tsc0) / ns : 0.0;
}

static size_t arg_size(int argc, char** argv, const std::string& key, size_t fallback) {
    for (int i = 1; i + 1 < argc; ++i) {
        if (argv[i] == key) {
            try { return static_cast<size_t>(std::stoull(argv[i + 1])); }
            catch (...) { std::cerr << "Invalid value for " << key << "\n"; std::exit(2); }
        }
    }
    return fallback;
}

static uint64_t percentile(const std::vector<uint64_t>& sorted, double p) {
    if (sorted.empty()) return 0;
    const size_t index = static_cast<size_t>(p * static_cast<double>(sorted.size() - 1));
    return sorted[index];
}

int main(int argc, char** argv) {
    const size_t warmup = arg_size(argc, argv, "--warmup", 200000);
    const size_t iterations = arg_size(argc, argv, "--iterations", 1000000);
    if (iterations < 1000 || warmup > 100000000) {
        std::cerr << "Use --iterations >= 1000 and --warmup <= 100000000.\n";
        return 2;
    }

    std::cout << "=== ARIES Tier 0: x86-64 cycle-level microbenchmark ===\n";
    int cpu = -1;
    if (pin_to_first_allowed_cpu(cpu))
        std::cout << "CPU affinity: pinned to allowed logical CPU " << cpu << "\n";
    else
        std::cout << "CPU affinity: FAILED (results may have additional scheduler noise)\n";

    const double tsc_ghz = calibrate_tsc_ghz();
    std::cout << std::fixed << std::setprecision(3)
              << "Measured TSC rate: " << tsc_ghz << " GHz-equivalent\n"
              << "Warmup iterations: " << warmup << "\n"
              << "Measured iterations: " << iterations << "\n";

    ARIESOperation op;
    volatile uint64_t sink = 0;
    for (size_t i = 0; i < warmup; ++i) sink = sink ^ op.evaluate();

    std::vector<uint64_t> samples;
    samples.reserve(iterations);
    // Each sample includes timestamp/fence overhead. Report raw cycles; do not
    // silently subtract a guessed overhead or claim this is end-to-end latency.
    for (size_t i = 0; i < iterations; ++i) {
        _mm_lfence();
        const uint64_t t0 = __rdtsc();
        _mm_lfence();
        const uint64_t result = op.evaluate();
        asm volatile("" : : "r"(result) : "memory");
        _mm_lfence();
        const uint64_t t1 = __rdtsc();
        _mm_lfence();
        sink = sink ^ result;
        samples.push_back(t1 - t0);
    }

    std::sort(samples.begin(), samples.end());
    const long double sum = std::accumulate(samples.begin(), samples.end(), 0.0L);
    const double mean = static_cast<double>(sum / samples.size());
    auto ns = [tsc_ghz](uint64_t cycles) {
        return tsc_ghz > 0 ? static_cast<double>(cycles) / tsc_ghz : 0.0;
    };

    std::cout << "\n--- Raw timestamp-window distribution (includes measurement overhead) ---\n"
              << "Min:  " << samples.front() << " cycles (" << ns(samples.front()) << " ns)\n"
              << "P50:  " << percentile(samples, 0.50) << " cycles ("
              << ns(percentile(samples, 0.50)) << " ns)\n"
              << "P99:  " << percentile(samples, 0.99) << " cycles ("
              << ns(percentile(samples, 0.99)) << " ns)\n"
              << "Max:  " << samples.back() << " cycles (" << ns(samples.back()) << " ns)\n"
              << "Mean: " << mean << " cycles (" << ns(static_cast<uint64_t>(mean)) << " ns)\n"
              << "Sink: " << sink << "\n"
              << "\nInterpretation: these are local microbenchmark measurements, not API/model latency.\n"
              << "A sub-1 ns displayed minimum does NOT establish sub-nanosecond operation latency;\n"
              << "timestamp overhead, TSC semantics, CPU model, compiler and environment matter.\n";
    return 0;
}
