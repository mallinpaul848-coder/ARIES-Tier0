#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <vector>

namespace AriesCore {

template <typename T, std::size_t Capacity>
class StaticMemoryPool {
    static_assert(Capacity > 0, "Capacity must be positive");
public:
    T* allocate() {
        if (used_ == Capacity) {
            throw std::bad_alloc();
        }
        return &buffer_[used_++];
    }

    void reset() noexcept { used_ = 0; }
    std::size_t used() const noexcept { return used_; }
    static constexpr std::size_t capacity() noexcept { return Capacity; }

private:
    alignas(64) T buffer_[Capacity]{};
    std::size_t used_ = 0;
};

class UnifiedExecutionEngine {
public:
    static std::vector<float> harmonic_transform(const std::vector<float>& input) {
        std::vector<float> output;
        output.reserve(input.size());
        for (float value : input) {
            if (!std::isfinite(value)) {
                throw std::invalid_argument("input values must be finite");
            }
            const float sign = value < 0.0f ? -1.0f : 1.0f;
            output.push_back(sign * std::cbrt(std::abs(value)) * (6.0f / 9.0f));
        }
        return output;
    }

    static bool validate_finite_state(const std::vector<float>& state) noexcept {
        for (float value : state) {
            if (!std::isfinite(value)) return false;
        }
        return true;
    }

    static std::vector<float> smooth_field(const std::vector<float>& field,
                                           float coefficient = 0.0001f) {
        if (!std::isfinite(coefficient) || coefficient < 0.0f || coefficient > 0.5f) {
            throw std::invalid_argument("coefficient must be finite and in [0, 0.5]");
        }
        if (!validate_finite_state(field)) {
            throw std::invalid_argument("field values must be finite");
        }
        if (field.size() < 3 || coefficient == 0.0f) return field;
        std::vector<float> result = field;
        for (std::size_t i = 1; i + 1 < field.size(); ++i) {
            result[i] = field[i] + coefficient *
                (field[i + 1] - 2.0f * field[i] + field[i - 1]);
        }
        return result;
    }
};

} // namespace AriesCore
