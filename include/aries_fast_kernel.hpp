#ifndef ARIES_FAST_KERNEL_HPP
#define ARIES_FAST_KERNEL_HPP

#include <array>
#include <cstddef>
#include <cstdint>

namespace aries::core {

// Byte residues and weights are retained for controlled experiments.
// 256 == 4 (mod 9), so the weights repeat 1, 4, 7.
inline constexpr std::array<std::uint8_t, 256> make_byte_remainder_table() noexcept {
    std::array<std::uint8_t, 256> table{};
    for (std::size_t i = 0; i < table.size(); ++i) {
        table[i] = static_cast<std::uint8_t>(i % 9);
    }
    return table;
}
inline constexpr auto byte_remainder_table = make_byte_remainder_table();
inline constexpr std::array<std::uint8_t, 8> byte_weights{1, 4, 7, 1, 4, 7, 1, 4};

// PRISE optimization: use the cheapest mathematically equivalent predicate.
// A positive integer has digital root 3, 6, or 9 iff it is divisible by 3.
// This avoids computing a full digital root when only the class is needed.
[[nodiscard]] constexpr bool is_harmonic_node_fast(std::uint64_t value) noexcept {
    return value != 0 && value % 3 == 0;
}

class UltraLowLatencyHarmonicEngine {
public:
    // Production digital root: compilers strength-reduce constant modulo.
    [[nodiscard]] static constexpr std::uint8_t fast_digital_root(std::uint64_t value) noexcept {
        if (value == 0) return 0;
        const auto remainder = static_cast<std::uint8_t>(value % 9);
        return remainder == 0 ? 9 : remainder;
    }

    // Experimental lookup path retained only for measured comparisons.
    [[nodiscard]] static constexpr std::uint8_t table_digital_root(std::uint64_t value) noexcept {
        if (value == 0) return 0;
        std::uint32_t remainder = 0;
        for (std::size_t i = 0; i < byte_weights.size(); ++i) {
            const auto byte_value = static_cast<std::uint8_t>(value >> (i * 8));
            remainder += byte_remainder_table[byte_value] * byte_weights[i];
        }
        remainder %= 9;
        return static_cast<std::uint8_t>(remainder == 0 ? 9 : remainder);
    }

    [[nodiscard]] static constexpr bool evaluate_harmonic_fast(
        std::uint64_t value, std::uint64_t& out_score) noexcept {
        const auto root = fast_digital_root(value);
        out_score = value * root; // Defined uint64_t wraparound, matching prior API.
        return is_harmonic_node_fast(value);
    }

    // Fused scan: one pass, no allocations, no digital-root work for the predicate.
    [[nodiscard]] static std::uint64_t count_harmonic_nodes(
        const std::uint64_t* values, std::size_t count) noexcept {
        if (values == nullptr) return 0;
        std::uint64_t matches = 0;
        for (std::size_t i = 0; i < count; ++i) {
            matches += static_cast<std::uint64_t>(is_harmonic_node_fast(values[i]));
        }
        return matches;
    }
};

} // namespace aries::core

#endif
