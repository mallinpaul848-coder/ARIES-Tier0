// ARIES native market-event microbenchmark.
// Synthetic decision-path test only: not exchange tick-to-trade or profitability evidence.
#include "aries_fast_kernel.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

namespace {
using Clock = std::chrono::steady_clock;
struct Event { std::int32_t delta, imbalance, risk; std::uint32_t size; };

Event make_event(std::uint64_t i) noexcept {
    return {
        static_cast<std::int32_t>((i * 37U) % 401U) - 200,
        static_cast<std::int32_t>((i * 19U) % 2001U) - 1000,
        static_cast<std::int32_t>((i * 13U) % 101U),
        static_cast<std::uint32_t>(1U + (i * 29U) % 10000U)
    };
}

std::int32_t baseline_decision(const Event& e) noexcept {
    if (e.risk >= 90) return 0;
    if (e.delta > 12 && e.imbalance > 150) return 1;
    if (e.delta < -12 && e.imbalance < -150) return -1;
    return 0;
}

struct Result {
    double wall_ms{}, cpu_ms{}, events_per_second{};
    double p50_ns{}, p95_ns{}, p99_ns{}, mean_ns{}, max_ns{};
    std::array<std::uint64_t, 3> actions{}; // hold, sell, buy
    std::uint64_t checksum{};
};

double percentile(const std::vector<double>& sorted, double p) {
    if (sorted.empty()) return 0.0;
    const double pos = (sorted.size() - 1) * p;
    const auto lo = static_cast<std::size_t>(pos);
    const auto hi = std::min(lo + 1, sorted.size() - 1);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

Result run(const std::vector<Event>& events, bool with_aries) {
    Result r;
    std::vector<double> latency;
    latency.reserve(events.size());
    const auto cpu_start = std::clock();
    const auto wall_start = Clock::now();
    for (const auto& e : events) {
        const auto start = Clock::now();
        const auto action = baseline_decision(e);
        if (with_aries) {
            const std::uint64_t magnitude =
                static_cast<std::uint64_t>(std::abs(e.delta)) +
                static_cast<std::uint64_t>(std::abs(e.imbalance)) +
                static_cast<std::uint64_t>(e.risk) + e.size;
            const auto root = aries::core::UltraLowLatencyHarmonicEngine::fast_digital_root(magnitude);
            const auto vortex = aries::core::vortex_phase_state(magnitude);
            // Integer PRISE-style feature score for profiling only; never changes action.
            const std::uint64_t feature_score =
                (static_cast<std::uint64_t>(e.size) + static_cast<std::uint64_t>(std::abs(e.delta)) +
                 static_cast<std::uint64_t>(std::abs(e.imbalance))) * (root + vortex);
            r.checksum += feature_score;
        } else {
            r.checksum += static_cast<std::uint64_t>(e.size) +
                          static_cast<std::uint64_t>(std::abs(e.delta));
        }
        r.actions[static_cast<std::size_t>(action + 1)]++;
        const auto end = Clock::now();
        latency.push_back(std::chrono::duration<double, std::nano>(end - start).count());
    }
    const auto wall_end = Clock::now();
    const auto cpu_end = std::clock();
    r.wall_ms = std::chrono::duration<double, std::milli>(wall_end - wall_start).count();
    r.cpu_ms = 1000.0 * static_cast<double>(cpu_end - cpu_start) / CLOCKS_PER_SEC;
    r.events_per_second = events.size() / (r.wall_ms / 1000.0);
    r.mean_ns = std::accumulate(latency.begin(), latency.end(), 0.0) / latency.size();
    r.max_ns = *std::max_element(latency.begin(), latency.end());
    std::sort(latency.begin(), latency.end());
    r.p50_ns = percentile(latency, 0.50);
    r.p95_ns = percentile(latency, 0.95);
    r.p99_ns = percentile(latency, 0.99);
    return r;
}

void print_result(const char* name, const Result& r) {
    std::cout << "  \"" << name << "\": {"
              << "\"wall_ms\":" << r.wall_ms << ","
              << "\"cpu_ms\":" << r.cpu_ms << ","
              << "\"events_per_second\":" << r.events_per_second << ","
              << "\"latency_ns\":{\"mean\":" << r.mean_ns
              << ",\"p50\":" << r.p50_ns << ",\"p95\":" << r.p95_ns
              << ",\"p99\":" << r.p99_ns << ",\"max\":" << r.max_ns << "},"
              << "\"actions\":{\"hold\":" << r.actions[1]
              << ",\"sell\":" << r.actions[0] << ",\"buy\":" << r.actions[2] << "},"
              << "\"checksum\":" << r.checksum << "}";
}
} // namespace

int main(int argc, char** argv) {
    std::uint64_t count = 500000;
    if (argc > 1) {
        try { count = std::stoull(argv[1]); }
        catch (...) { std::cerr << "events must be a positive integer\n"; return 2; }
    }
    if (count == 0 || count > 10000000) {
        std::cerr << "events must be between 1 and 10000000\n";
        return 2;
    }
    std::vector<Event> events;
    events.reserve(static_cast<std::size_t>(count));
    for (std::uint64_t i = 0; i < count + 5000; ++i) {
        const auto e = make_event(i);
        if (i >= 5000) events.push_back(e);
        else { (void)baseline_decision(e); }
    }
    const auto baseline = run(events, false);
    const auto aries = run(events, true);
    const bool parity = baseline.actions == aries.actions;
    std::cout << std::fixed << std::setprecision(3)
              << "{\"suite\":\"ARIES native synthetic market-event benchmark\","
              << "\"events\":" << count << ","
              << "\"scope\":\"single-process decision-path microbenchmark; not exchange HFT\","
              << "\"action_counts_match\":" << (parity ? "true" : "false") << ","
              << "\"baseline\":";
    print_result("baseline", baseline);
    std::cout << ",\"aries_feature_path\":";
    print_result("aries_feature_path", aries);
    std::cout << ",\"interpretation\":["
              << "\"Feature descriptors do not change the baseline trading action.\","
              << "\"Per-event timings include clock-call overhead.\","
              << "\"No network, order routing, fills, PnL, or calibrated energy measurement.\"]}\n";
    return parity ? 0 : 3;
}
