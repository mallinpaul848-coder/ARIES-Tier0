#pragma once

// Mallin Master Platform primitives for ARIES Tier 0.
// C++20. The ring buffer is strictly single-producer/single-consumer (SPSC).
// This module does not claim sub-nanosecond end-to-end inference.

#include <array>
#include <atomic>
#include <bit>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <new>
#include <type_traits>
#include <utility>

namespace mallin::master {

inline constexpr std::size_t cache_line_bytes = 64;

struct LicenseToken {
    std::uint64_t client_id{};
    std::uint64_t hardware_node_hash{};
    std::uint64_t expiration_timestamp{};
    // Signature bytes are supplied/verified by the application's crypto layer.
    // A nonzero integer is NOT a cryptographic signature.
    std::array<std::uint8_t, 64> signature{};
};

using SignatureVerifier = bool (*)(const LicenseToken&, void*) noexcept;

// Fail closed: identity, hardware binding, expiry and a real caller-supplied
// signature verifier are required. The verifier should use a maintained crypto
// library and a trusted public key; do not implement signature crypto here.
[[nodiscard]] inline bool verify_license(
    const LicenseToken& token,
    std::uint64_t current_timestamp,
    std::uint64_t expected_hardware_node_hash,
    SignatureVerifier verifier,
    void* verifier_context = nullptr) noexcept {
    if (token.client_id == 0 || token.hardware_node_hash == 0 ||
        token.hardware_node_hash != expected_hardware_node_hash ||
        token.expiration_timestamp < current_timestamp ||
        verifier == nullptr) {
        return false;
    }
    bool has_signature_byte = false;
    for (const auto byte : token.signature) {
        has_signature_byte = has_signature_byte || byte != 0;
    }
    return has_signature_byte && verifier(token, verifier_context);
}

class UnifiedFrequencyEngine {
public:
    static constexpr double golden_ratio = 1.618033988749895;
    static constexpr double tesla_base_frequency_hz = 432.0;

    // Mathematical feature generator only; it does not establish physical
    // resonance, a universal frequency, or an inference speedup.
    [[nodiscard]] static double compute_harmonic_node(
        double scale_factor, std::uint32_t multiplier) noexcept {
        if (!std::isfinite(scale_factor) || scale_factor <= 0.0 || multiplier == 0) {
            return std::numeric_limits<double>::quiet_NaN();
        }
        return tesla_base_frequency_hz * static_cast<double>(multiplier) *
               std::cbrt(scale_factor * golden_ratio);
    }
};

struct alignas(cache_line_bytes) MasterPayload {
    std::uint64_t sequence_id{};
    std::uint64_t timestamp_cycles{};
    std::uint32_t payload_type{0x369};
    std::uint32_t actuation_flags{};
    std::array<double, 4> harmonic_spatial_vector{};
};

// SPSC ring buffer. Exactly one thread may call try_dispatch and exactly one
// other thread may call try_pop. Capacity must be a power of two and at least 2.
// Uses optional-like raw storage so T lifetimes are started/ended correctly.
// T must be nothrow destructible; methods catch construction/assignment errors
// by contract only where stated. For low-latency use, prefer nothrow T types.
template <typename T, std::size_t Capacity>
requires (Capacity >= 2 && std::has_single_bit(Capacity) &&
          std::is_nothrow_destructible_v<T>)
class LicensedLockFreeRingBuffer {
    struct Slot {
        alignas(T) std::byte storage[sizeof(T)];
        T* ptr() noexcept { return std::launder(reinterpret_cast<T*>(storage)); }
    };

public:
    LicensedLockFreeRingBuffer() noexcept = default;
    LicensedLockFreeRingBuffer(const LicensedLockFreeRingBuffer&) = delete;
    LicensedLockFreeRingBuffer& operator=(const LicensedLockFreeRingBuffer&) = delete;

    ~LicensedLockFreeRingBuffer() noexcept {
        // Destruction must occur after producer and consumer have stopped.
        auto head = head_.load(std::memory_order_relaxed);
        const auto tail = tail_.load(std::memory_order_relaxed);
        while (head != tail) {
            slots_[head & mask].ptr()->~T();
            ++head;
        }
    }

    template <typename... Args>
    bool try_dispatch(const LicenseToken& token,
                      std::uint64_t current_timestamp,
                      std::uint64_t expected_hardware_node_hash,
                      SignatureVerifier verifier,
                      void* verifier_context,
                      Args&&... args) {
        if (!verify_license(token, current_timestamp, expected_hardware_node_hash,
                            verifier, verifier_context)) {
            return false;
        }

        const auto tail = tail_.load(std::memory_order_relaxed);
        const auto head = head_.load(std::memory_order_acquire);
        if (tail - head >= Capacity) {
            return false;
        }

        ::new (static_cast<void*>(slots_[tail & mask].storage))
            T(std::forward<Args>(args)...);
        tail_.store(tail + 1, std::memory_order_release);
        return true;
    }

    bool try_pop(T& value) noexcept(std::is_nothrow_move_assignable_v<T> ||
                                    std::is_nothrow_copy_assignable_v<T>) {
        const auto head = head_.load(std::memory_order_relaxed);
        const auto tail = tail_.load(std::memory_order_acquire);
        if (head == tail) {
            return false;
        }
        T* item = slots_[head & mask].ptr();
        value = std::move_if_noexcept(*item);
        item->~T();
        head_.store(head + 1, std::memory_order_release);
        return true;
    }

    [[nodiscard]] std::size_t size_approx() const noexcept {
        const auto tail = tail_.load(std::memory_order_acquire);
        const auto head = head_.load(std::memory_order_acquire);
        return tail >= head ? tail - head : 0;
    }

    [[nodiscard]] static constexpr std::size_t capacity() noexcept { return Capacity; }

private:
    static constexpr std::size_t mask = Capacity - 1;
    std::array<Slot, Capacity> slots_{};
    alignas(cache_line_bytes) std::atomic<std::size_t> head_{0};
    alignas(cache_line_bytes) std::atomic<std::size_t> tail_{0};
};

} // namespace mallin::master
