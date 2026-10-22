from fastapi.testclient import TestClient
from api.main import app, chat_completions_url

client = TestClient(app)


def test_health_is_available():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_models_endpoint_does_not_fabricate_model():
    response = client.get("/v1/models")
    assert response.status_code == 200
    assert response.json()["object"] == "list"
    assert response.json()["data"] == []
    assert response.json()["inference_ready"] is False


def test_supported_arithmetic_works_without_upstream_backend():
    response = client.post("/v1/chat/completions", json={
        "model": "aries",
        "messages": [{"role": "user", "content": "2+2?"}]
    })
    assert response.status_code == 200
    body = response.json()
    assert body["choices"][0]["message"]["content"] == "4"
    assert body["aries_runtime"]["deterministic"] is True


def test_mallin_369_math_routes_through_chat():
    response = client.post("/v1/chat/completions", json={
        "model": "aries",
        "messages": [{"role": "user", "content": "What is the digital root of 18?"}]
    })
    assert response.status_code == 200
    body = response.json()
    assert body["aries_runtime"]["route"] == "digital_root_369"
    assert '"digital_root": 9' in body["choices"][0]["message"]["content"]


def test_unsupported_chat_still_requires_real_inference_backend():
    response = client.post("/v1/chat/completions", json={
        "model": "aries",
        "messages": [{"role": "user", "content": "Explain the history of the Roman Empire."}]
    })
    assert response.status_code == 503
    assert "not fully configured" in response.json()["detail"]


def test_mallin_research_api_lists_all_six_prize_problem_routes():
    response = client.get("/v8/research/problems")
    assert response.status_code == 200
    body = response.json()
    assert len(body["problems"]) == 6
    assert "PRISE" in body["operators"]
    assert "digital_root_369" in body["operators"]


def test_mallin_research_analysis_returns_auditable_exploratory_result():
    response = client.post("/v8/research/analyze", json={
        "problem": "P vs NP",
        "values": [3, 6, 9, 12],
        "priority": 1,
        "risk": 1,
        "impact": 1,
        "systemic": 1,
        "emergent": 1
    })
    assert response.status_code == 200
    body = response.json()
    assert body["problem"] == "P_VS_NP"
    assert body["proof_claim"] is False
    assert body["evidence_status"] == "exploratory_only"
    assert len(body["fingerprint_sha256"]) == 64


def test_chat_url_does_not_duplicate_v1():
    assert chat_completions_url("https://provider.example/v1") == (
        "https://provider.example/v1/chat/completions"
    )


def test_chat_url_adds_v1_when_missing():
    assert chat_completions_url("https://provider.example") == (
        "https://provider.example/v1/chat/completions"
    )
