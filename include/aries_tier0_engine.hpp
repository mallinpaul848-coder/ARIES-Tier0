#ifndef ARIES_TIER0_ENGINE_HPP
#define ARIES_TIER0_ENGINE_HPP

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace aries::core {

// Bounded single-producer/single-consumer queue. The producer must be the only
// caller of push(); the consumer must be the only caller of pop().
template <std::size_t Capacity>
class AriesDeterministicEngine {
    static_assert(Capacity > 0, "Capacity must be greater than zero");
    static_assert((Capacity & (Capacity - 1)) == 0,
                  "Capacity must be a power of two");
    static_assert(Capacity <= (std::numeric_limits<std::size_t>::max() / 2),
                  "Capacity must be less than half the cursor range");

    struct Node {
        std::uint64_t raw_payload{};
        std::uint64_t harmonic_score{};
        bool is_harmonic{};
    };

    // 64 bytes is a common cache-line size, not a universal hardware guarantee.
    struct alignas(64) Cursor {
        std::atomic<std::size_t> value{0};
    };

    std::array<Node, Capacity> ring_{};
    Cursor head_{};
    Cursor tail_{};

    [[nodiscard]] static constexpr std::uint8_t digital_root(
        std::uint64_t value) noexcept {
        if (value == 0) return 0;
        const auto remainder = static_cast<std::uint8_t>(value % 9U);
        return remainder == 0 ? 9 : remainder;
    }

public:
    AriesDeterministicEngine() noexcept = default;
    AriesDeterministicEngine(const AriesDeterministicEngine&) = delete;
    AriesDeterministicEngine& operator=(const AriesDeterministicEngine&) = delete;
    AriesDeterministicEngine(AriesDeterministicEngine&&) = delete;
    AriesDeterministicEngine& operator=(AriesDeterministicEngine&&) = delete;

    // SPSC only. Returns false when the bounded queue is full.
    [[nodiscard]] bool push(std::uint64_t payload) noexcept {
        const auto tail = tail_.value.load(std::memory_order_relaxed);
        const auto head = head_.value.load(std::memory_order_acquire);
        if (tail - head >= Capacity) return false;

        const auto root = digital_root(payload);
        const Node node{
            payload,
            payload * static_cast<std::uint64_t>(root), // unsigned wrap is defined
            payload != 0 && payload % 3U == 0U
        };

        ring_[tail & (Capacity - 1)] = node;
        tail_.value.store(tail + 1, std::memory_order_release);
        return true;
    }

    // SPSC only. Returns false when the bounded queue is empty.
    [[nodiscard]] bool pop(std::uint64_t& out_payload,
                           std::uint64_t& out_score,
                           bool& out_is_harmonic) noexcept {
        const auto head = head_.value.load(std::memory_order_relaxed);
        const auto tail = tail_.value.load(std::memory_order_acquire);
        if (head == tail) return false;

        const Node node = ring_[head & (Capacity - 1)];
        out_payload = node.raw_payload;
        out_score = node.harmonic_score;
        out_is_harmonic = node.is_harmonic;
        head_.value.store(head + 1, std::memory_order_release);
        return true;
    }

    [[nodiscard]] static constexpr std::size_t capacity() noexcept {
        return Capacity;
    }

    // Lock-free behavior is implementation-dependent; check the actual atomics.
    [[nodiscard]] bool atomics_are_lock_free() const noexcept {
        return head_.value.is_lock_free() && tail_.value.is_lock_free();
    }
};

} // namespace aries::core

#endif // ARIES_TIER0_ENGINE_HPP
