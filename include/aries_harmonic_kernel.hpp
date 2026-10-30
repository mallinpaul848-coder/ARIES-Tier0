#ifndef ARIES_HARMONIC_KERNEL_HPP
#define ARIES_HARMONIC_KERNEL_HPP

#include <array>
#include <cstddef>
#include <cstdint>

namespace aries::core {

[[nodiscard]] constexpr std::uint8_t compute_digital_root(std::uint64_t n) noexcept {
    if (n == 0) return 0;
    const auto remainder = static_cast<std::uint8_t>(n % 9);
    return remainder == 0 ? 9 : remainder;
}

// This is a digital-root class filter, not a primality test.
// For positive integers, roots 3, 6, and 9 are exactly multiples of 3.
[[nodiscard]] constexpr bool is_harmonic_node(std::uint64_t value) noexcept {
    const auto root = compute_digital_root(value);
    return root == 3 || root == 6 || root == 9;
}

// Fixed-capacity, allocation-free FIFO for single-threaded use.
// No atomics are used: this type is deliberately NOT thread-safe or lock-free.
template <std::size_t Capacity>
class DeterministicHarmonicFilter {
    static_assert(Capacity > 0, "Capacity must be greater than zero");

public:
    [[nodiscard]] bool push(std::uint64_t value) noexcept {
        if (count_ == Capacity) return false;
        buffer_[tail_] = value;
        tail_ = (tail_ + 1) % Capacity;
        ++count_;
        return true;
    }

    [[nodiscard]] bool process_next(std::uint64_t& out_weighted_score) noexcept {
        if (count_ == 0) return false;
        const std::uint64_t value = buffer_[head_];
        head_ = (head_ + 1) % Capacity;
        --count_;
        out_weighted_score = value * compute_digital_root(value);
        return true;
    }

    [[nodiscard]] constexpr std::size_t size() const noexcept { return count_; }
    [[nodiscard]] constexpr bool empty() const noexcept { return count_ == 0; }
    [[nodiscard]] static constexpr std::size_t capacity() noexcept { return Capacity; }

private:
    std::array<std::uint64_t, Capacity> buffer_{};
    std::size_t head_{0};
    std::size_t tail_{0};
    std::size_t count_{0};
};

} // namespace aries::core

#endif
