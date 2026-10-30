#include "aries_fast_kernel.hpp"
#include "aries_harmonic_kernel.hpp"

#include <cassert>
#include <cstdint>

int main() {
    using aries::core::UltraLowLatencyHarmonicEngine;
    using aries::core::compute_digital_root;

    for (std::uint64_t value = 0; value < 100000; ++value) {
        assert(UltraLowLatencyHarmonicEngine::fast_digital_root(value) ==
               compute_digital_root(value));
    }

    constexpr std::uint64_t values[] = {
        0, 1, 2, 3, 6, 9, 10, 18, 255, 256, 257,
        0xFFFFFFFFFFFFFFFFULL, 0x8000000000000000ULL
    };
    for (const auto value : values) {
        assert(UltraLowLatencyHarmonicEngine::fast_digital_root(value) ==
               compute_digital_root(value));
        assert(UltraLowLatencyHarmonicEngine::table_digital_root(value) ==
               compute_digital_root(value));
    }

    std::uint64_t score = 0;
    assert(UltraLowLatencyHarmonicEngine::evaluate_harmonic_fast(12, score));
    assert(score == 36);
    assert(!UltraLowLatencyHarmonicEngine::evaluate_harmonic_fast(10, score));
    assert(score == 10);
    return 0;
}
