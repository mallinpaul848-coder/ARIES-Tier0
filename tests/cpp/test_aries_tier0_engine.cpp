#include "aries_tier0_engine.hpp"
#include "aries_fast_kernel.hpp"
#include "aries_harmonic_kernel.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <limits>

int main() {
    using aries::core::AriesDeterministicEngine;
    AriesDeterministicEngine<4> queue;
    static_assert(AriesDeterministicEngine<4>::capacity() == 4);

    std::uint64_t payload = 0, score = 0;
    bool harmonic = false;
    assert(!queue.pop(payload, score, harmonic));

    assert(queue.push(0));
    assert(queue.push(3));
    assert(queue.push(10));
    assert(queue.push(18));
    assert(!queue.push(21)); // full

    assert(queue.pop(payload, score, harmonic));
    assert(payload == 0 && score == 0 && !harmonic);
    assert(queue.pop(payload, score, harmonic));
    assert(payload == 3 && score == 9 && harmonic);
    assert(queue.pop(payload, score, harmonic));
    assert(payload == 10 && score == 10 && !harmonic);
    assert(queue.pop(payload, score, harmonic));
    assert(payload == 18 && score == 162 && harmonic);
    assert(!queue.pop(payload, score, harmonic));

    // Exercise repeated wraparound and compare harmonic classification against
    // ARIES's existing reference implementation.
    for (std::uint64_t i = 0; i < 100000; ++i) {
        assert(queue.push(i));
        assert(queue.pop(payload, score, harmonic));
        assert(payload == i);
        assert(score == i * aries::core::compute_digital_root(i));
        assert(harmonic == aries::core::is_harmonic_node(i));
    }

    assert(queue.push(std::numeric_limits<std::uint64_t>::max()));
    assert(queue.pop(payload, score, harmonic));
    assert(payload == std::numeric_limits<std::uint64_t>::max());
    assert(score == payload * aries::core::compute_digital_root(payload));
    assert(harmonic == aries::core::is_harmonic_node(payload));

    // A 1-slot queue is valid and tests the minimum power-of-two capacity.
    AriesDeterministicEngine<1> single;
    assert(single.push(9));
    assert(!single.push(3));
    assert(single.pop(payload, score, harmonic));
    assert(payload == 9 && score == 81 && harmonic);
    return 0;
}
