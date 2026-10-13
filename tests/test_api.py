from fastapi.testclient import TestClient
from api.main import app

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

def test_chat_requires_real_backend():
    response = client.post("/v1/chat/completions", json={
        "model": "aries",
        "messages": [{"role": "user", "content": "2+2?"}]
    })
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]
