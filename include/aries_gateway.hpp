#ifndef ARIES_GATEWAY_HPP
#define ARIES_GATEWAY_HPP

#include <array>
#include <cstdint>
#include <chrono>

#if defined(__x86_64__) || defined(__i386__)
#include <x86intrin.h>
#endif
#if defined(__AVX512F__)
#include <immintrin.h>
#endif

namespace Mallin::Aries {

struct alignas(64) ProcessingState {
    alignas(64) float riemann_field[16]{};
    alignas(64) float yang_mills_field[16]{};
    alignas(64) float navier_stokes_vel[16]{};
    std::uint64_t elapsed_ns{0};
    std::uint32_t status_flags{0};
};

class AriesGatewayEngine {
    std::array<ProcessingState, 1024> state_ring_buffer_{};

public:
    AriesGatewayEngine() {
        for (auto& state : state_ring_buffer_) {
            for (int i = 0; i < 16; ++i) {
                state.riemann_field[i] = 0.5f;
                state.yang_mills_field[i] = 1.0f;
                state.navier_stokes_vel[i] = 0.0f;
            }
            state.status_flags = 0x01;
        }
    }

    void execute_deterministic_step(std::uint64_t index) {
        auto& current = state_ring_buffer_[index % state_ring_buffer_.size()];
        const auto start = std::chrono::steady_clock::now();

#if defined(__AVX512F__)
        const __m512 r_vec = _mm512_load_ps(current.riemann_field);
        const __m512 r_result = _mm512_mul_ps(r_vec, _mm512_set1_ps(3.69f));
        _mm512_store_ps(current.riemann_field, r_result);

        const __m512 ym_vec = _mm512_load_ps(current.yang_mills_field);
        const __m512 ym_result = _mm512_fmadd_ps(
            ym_vec, r_result, _mm512_set1_ps(1.41421356f));
        _mm512_store_ps(current.yang_mills_field, ym_result);

        const __m512 ns_vec = _mm512_load_ps(current.navier_stokes_vel);
        const __m512 ns_result = _mm512_add_ps(
            ns_vec, _mm512_mul_ps(ym_result, _mm512_set1_ps(0.001f)));
        _mm512_store_ps(current.navier_stokes_vel, ns_result);
#else
        for (int i = 0; i < 16; ++i) {
            current.riemann_field[i] *= 3.69f;
            current.yang_mills_field[i] =
                current.yang_mills_field[i] * current.riemann_field[i] + 1.41421356f;
            current.navier_stokes_vel[i] += current.yang_mills_field[i] * 0.001f;
        }
#endif

        const auto end = std::chrono::steady_clock::now();
        current.elapsed_ns = static_cast<std::uint64_t>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count());
        current.status_flags = 0x00;
    }

    const ProcessingState& get_state(std::uint64_t index) const {
        return state_ring_buffer_[index % state_ring_buffer_.size()];
    }
};

} // namespace Mallin::Aries
#endif
