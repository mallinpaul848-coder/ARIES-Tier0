// ARIES-Tier0 deterministic microbenchmark.
// This measures a tiny integer operation plus timer/fence overhead; it is NOT
// a model-inference benchmark and must not be described as sub-nanosecond AI.
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>
#if defined(__x86_64__) || defined(__i386__)
#include <x86intrin.h>
#endif

static inline uint64_t ticks_begin() {
#if defined(__x86_64__) || defined(__i386__)
  _mm_lfence();
  const uint64_t t = __rdtsc();
  _mm_lfence();
  return t;
#else
  return 0;
#endif
}
static inline uint64_t ticks_end() {
#if defined(__x86_64__) || defined(__i386__)
  _mm_lfence();
  const uint64_t t = __rdtsc();
  _mm_lfence();
  return t;
#else
  return 0;
#endif
}
static double percentile(const std::vector<double>& sorted, double p) {
  if (sorted.empty()) return 0.0;
  const auto i = static_cast<size_t>(p * static_cast<double>(sorted.size()-1));
  return sorted[std::min(i, sorted.size()-1)];
}
int main(int argc, char** argv) {
#if !defined(__x86_64__) && !defined(__i386__)
  std::cerr << "This cycle benchmark requires an x86/x86-64 TSC.\n";
  return 2;
#endif
  size_t n = 10000;
  if (argc > 1) n = static_cast<size_t>(std::strtoull(argv[1], nullptr, 10));
  if (n < 100) { std::cerr << "iterations must be >= 100\n"; return 2; }
  volatile uint64_t sink = 0;
  for (size_t i=0; i<1000; ++i) sink = sink + ((i * 17u + 19u) % 997u);
  std::vector<double> samples;
  samples.reserve(n);
  for (size_t i=0; i<n; ++i) {
    const uint64_t a = ticks_begin();
    const uint64_t x = static_cast<uint64_t>(i);
    const uint64_t result = (x * 17u + 19u) % 997u;
    const uint64_t b = ticks_end();
    sink = sink + result;
    samples.push_back(static_cast<double>(b-a));
  }
  std::sort(samples.begin(), samples.end());
  const double mean = std::accumulate(samples.begin(), samples.end(), 0.0) / samples.size();
  std::ofstream csv("aries_microbenchmark_samples.csv");
  csv << "sample_index,tsc_ticks\n";
  for (size_t i=0; i<samples.size(); ++i) csv << i << "," << std::fixed << std::setprecision(0) << samples[i] << "\n";
  std::cout << std::fixed << std::setprecision(3)
            << "benchmark=deterministic_integer_micro_op\n"
            << "iterations=" << n << "\n"
            << "units=tsc_ticks (not guaranteed core cycles)\n"
            << "min_ticks=" << samples.front() << "\n"
            << "p50_ticks=" << percentile(samples, .50) << "\n"
            << "p99_ticks=" << percentile(samples, .99) << "\n"
            << "mean_ticks=" << mean << "\n"
            << "max_ticks=" << samples.back() << "\n"
            << "sink=" << sink << "\n"
            << "limitation=includes timer/fence overhead; not AI inference; TSC ticks are not automatically nanoseconds\n";
  return 0;
}
