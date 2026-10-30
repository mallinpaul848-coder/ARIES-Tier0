#include "aries_fast_kernel.hpp"
#include "aries_harmonic_kernel.hpp"

#include <array>
#include <cassert>
#include <cstdint>

int main() {
    using aries::core::UltraLowLatencyHarmonicEngine;
    using aries::core::compute_digital_root;
    using aries::core::vortex_phase_state;

    for (std::uint64_t value = 0; value < 100000; ++value) {
        assert(UltraLowLatencyHarmonicEngine::fast_digital_root(value) ==
               compute_digital_root(value));
        assert(aries::core::is_harmonic_node_fast(value) ==
               aries::core::is_harmonic_node(value));
    }

    constexpr std::uint64_t values[] = {
        0, 1, 2, 3, 6, 9, 10, 18, 255, 256, 257,
        0xFFFFFFFFFFFFFFFFULL, 0x8000000000000000ULL
    };
    for (const auto value : values) {
        assert(UltraLowLatencyHarmonicEngine::fast_digital_root(value) ==
               compute_digital_root(value));
        assert(aries::core::is_harmonic_node_fast(value) ==
               aries::core::is_harmonic_node(value));
        assert(UltraLowLatencyHarmonicEngine::table_digital_root(value) ==
               compute_digital_root(value));
    }

    std::uint64_t score = 0;
    assert(UltraLowLatencyHarmonicEngine::evaluate_harmonic_fast(12, score));
    assert(score == 36);
    assert(!UltraLowLatencyHarmonicEngine::evaluate_harmonic_fast(10, score));
    assert(score == 10);

    constexpr std::array<std::uint64_t, 7> batch{0, 3, 6, 9, 10, 12, 14};
    assert(UltraLowLatencyHarmonicEngine::count_harmonic_nodes(
        batch.data(), batch.size()) == 4);
    assert(UltraLowLatencyHarmonicEngine::count_harmonic_nodes(nullptr, 7) == 0);

    constexpr std::array<std::uint8_t, 6> vortex{1, 2, 4, 8, 7, 5};
    for (std::uint64_t step = 0; step < 600; ++step) {
        assert(vortex_phase_state(step) == vortex[step % vortex.size()]);
    }
    return 0;
}
