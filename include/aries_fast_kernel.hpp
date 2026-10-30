#ifndef ARIES_FAST_KERNEL_HPP
#define ARIES_FAST_KERNEL_HPP

#include <array>
#include <cstddef>
#include <cstdint>

namespace aries::core {

// Remainder lookup for a byte. The result is in [0, 8], with zero preserved.
inline constexpr std::array<std::uint8_t, 256> make_byte_remainder_table() noexcept {
    std::array<std::uint8_t, 256> table{};
    for (std::size_t i = 0; i < table.size(); ++i) {
        table[i] = static_cast<std::uint8_t>(i % 9);
    }
    return table;
}

inline constexpr auto byte_remainder_table = make_byte_remainder_table();

inline constexpr std::array<std::uint8_t, 449> make_root_table() noexcept {
    std::array<std::uint8_t, 449> table{};
    for (std::size_t i = 0; i < table.size(); ++i) {
        const auto remainder = static_cast<std::uint8_t>(i % 9);
        table[i] = remainder == 0 ? 9 : remainder;
    }
    return table;
}

inline constexpr auto root_table = make_root_table();

// 256^i modulo 9 repeats as 1, 4, 7 because 256 == 4 (mod 9).
inline constexpr std::array<std::uint8_t, 8> byte_weights{
    1, 4, 7, 1, 4, 7, 1, 4
};

class UltraLowLatencyHarmonicEngine {
public:
    // Eight byte-table lookups and a bounded final reduction; no runtime
    // division or data-dependent loop. This is O(1), but not guaranteed
    // sub-nanosecond: actual latency depends on compiler and CPU.
    [[nodiscard]] static constexpr std::uint8_t fast_digital_root(std::uint64_t value) noexcept {
        std::uint32_t remainder = 0;
        for (std::size_t i = 0; i < byte_weights.size(); ++i) {
            const auto byte_value = static_cast<std::uint8_t>(value >> (i * 8));
            remainder += byte_remainder_table[byte_value] * byte_weights[i];
        }
        remainder %= 9;
        return value == 0 ? 0 : static_cast<std::uint8_t>(remainder == 0 ? 9 : remainder);
    }

    [[nodiscard]] static constexpr bool evaluate_harmonic_fast(
        std::uint64_t value, std::uint64_t& out_score) noexcept {
        const auto root = fast_digital_root(value);
        out_score = value * root;
        constexpr std::uint16_t harmonic_mask =
            (std::uint16_t{1} << 3) | (std::uint16_t{1} << 6) | (std::uint16_t{1} << 9);
        return (harmonic_mask & (std::uint16_t{1} << root)) != 0;
    }
};

} // namespace aries::core

#endif
