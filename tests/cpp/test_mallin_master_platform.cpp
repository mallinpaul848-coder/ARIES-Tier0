#include "platform/native/mallin_master_platform.hpp"

#include <cassert>
#include <cmath>
#include <cstdint>

using namespace mallin::master;

static bool test_signature_verifier(const LicenseToken& token, void*) noexcept {
    return token.signature[0] == 0xA5;
}

int main() {
    LicenseToken token{};
    token.client_id = 7;
    token.hardware_node_hash = 1234;
    token.expiration_timestamp = 5000;
    token.signature[0] = 0xA5;

    assert(verify_license(token, 1000, 1234, test_signature_verifier));
    assert(!verify_license(token, 5001, 1234, test_signature_verifier));
    assert(!verify_license(token, 1000, 9999, test_signature_verifier));
    assert(!verify_license(token, 1000, 1234, nullptr));

    const double node = UnifiedFrequencyEngine::compute_harmonic_node(1.0, 3);
    assert(std::isfinite(node) && node > 0.0);
    assert(std::isnan(UnifiedFrequencyEngine::compute_harmonic_node(-1.0, 3)));
    assert(std::isnan(UnifiedFrequencyEngine::compute_harmonic_node(1.0, 0)));

    LicensedLockFreeRingBuffer<int, 2> queue;
    int out = 0;
    assert(!queue.try_pop(out));
    assert(queue.try_dispatch(token, 1000, 1234, test_signature_verifier, nullptr, 11));
    assert(queue.try_dispatch(token, 1000, 1234, test_signature_verifier, nullptr, 22));
    assert(!queue.try_dispatch(token, 1000, 1234, test_signature_verifier, nullptr, 33));
    assert(queue.size_approx() == 2);
    assert(queue.try_pop(out) && out == 11);
    assert(queue.try_pop(out) && out == 22);
    assert(!queue.try_pop(out));

    assert(!queue.try_dispatch(token, 6000, 1234, test_signature_verifier, nullptr, 44));
    return 0;
}
