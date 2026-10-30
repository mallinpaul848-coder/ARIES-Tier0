#include "aries_harmonic_kernel.hpp"

#include <cassert>
#include <cstdint>

int main() {
    using aries::core::compute_digital_root;
    using aries::core::is_harmonic_node;
    using aries::core::DeterministicHarmonicFilter;

    static_assert(compute_digital_root(0) == 0);
    static_assert(compute_digital_root(18) == 9);
    static_assert(is_harmonic_node(3));
    static_assert(is_harmonic_node(12));
    static_assert(!is_harmonic_node(5));

    DeterministicHarmonicFilter<2> queue;
    std::uint64_t score = 0;
    assert(queue.empty());
    assert(!queue.process_next(score));
    assert(queue.push(3));
    assert(queue.push(10));
    assert(!queue.push(12));
    assert(queue.size() == 2);
    assert(queue.process_next(score) && score == 9);
    assert(queue.process_next(score) && score == 10);
    assert(!queue.process_next(score));
    assert(queue.empty());
    return 0;
}
