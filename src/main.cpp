#include "aries_gateway.hpp"
#include <iostream>

int main() {
    Mallin::Aries::AriesGatewayEngine engine;
    std::cout << "[MALLIN PROGRAM] ARIES deterministic arithmetic demo initialized.\n";
    constexpr std::uint64_t test_index = 0;
    engine.execute_deterministic_step(test_index);

    const auto& result = engine.get_state(test_index);
    std::cout << "[DEMO] elapsed_ns=" << result.elapsed_ns << "\n";
    std::cout << "[DEMO] Riemann-labelled field[0]=" << result.riemann_field[0] << "\n";
    std::cout << "[DEMO] Yang-Mills-labelled field[0]=" << result.yang_mills_field[0] << "\n";
    std::cout << "[DEMO] Navier-Stokes-labelled field[0]=" << result.navier_stokes_vel[0] << "\n";
    std::cout << "[NOTE] These are illustrative arithmetic fields, not validated mathematical solvers.\n";
    return 0;
}
