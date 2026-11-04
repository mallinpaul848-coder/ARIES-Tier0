import pytest

from aries_math.gateway_optimizer import analyze_gateway_request


def test_gateway_profile_is_deterministic_and_preserves_case():
    first = analyze_gateway_request("  Optimize   ARIES latency  ")
    second = analyze_gateway_request("Optimize ARIES latency")
    lower = analyze_gateway_request("optimize aries latency")
    assert first["fingerprint_sha256"] == second["fingerprint_sha256"]
    assert first["fingerprint_sha256"] != lower["fingerprint_sha256"]
    assert first["harmonic"]["byte_sum_digital_root"] in range(10)


def test_gateway_profile_merges_prise_369_phase8_and_helixo():
    result = analyze_gateway_request("Urgent: benchmark Gateway integration; research latency.")
    assert result["prise"]["profile"]["priority"] == 1.0
    assert result["prise"]["profile"]["impact"] == 1.0
    assert result["harmonic"]["phase8"]["phase"] in range(8)
    assert result["harmonic"]["helixo"]["count"] == 4
    assert result["routing"]["hint"] == "reasoning_scaffold_candidate"
    assert result["routing"]["hint_is_advisory"] is True


def test_high_risk_is_flagged_without_claiming_answer_correctness():
    result = analyze_gateway_request("Review this production security credential change.")
    assert result["routing"]["high_risk_review_flag"] is True
    assert result["routing"]["hint"] == "review_first"
    assert result["prise"]["score_is_probability"] is False


def test_gateway_profile_rejects_non_string_prompt():
    with pytest.raises(TypeError):
        analyze_gateway_request(None)
