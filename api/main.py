# ARIES public gateway: real inference requires an explicitly configured upstream backend.
import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="ARIES AI API", version="1.0.4")

MODEL_ID = os.getenv("ARIES_MODEL_ID", "").strip()
UPSTREAM_BASE_URL = os.getenv("ARIES_UPSTREAM_BASE_URL", "").strip().rstrip("/")
UPSTREAM_API_KEY = os.getenv("ARIES_UPSTREAM_API_KEY", "").strip()
try:
    UPSTREAM_TIMEOUT_SECONDS = max(
        1.0, min(float(os.getenv("ARIES_UPSTREAM_TIMEOUT_SECONDS", "90")), 300.0)
    )
except ValueError:
    UPSTREAM_TIMEOUT_SECONDS = 90.0


def chat_completions_url(base_url: str) -> str:
    """Accept a provider root, an /v1 base URL, or the full chat-completions URL."""
    normalized = base_url.strip().rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/chat/completions"
    return f"{normalized}/v1/chat/completions"


class Message(BaseModel):
    role: str = Field(min_length=1, max_length=40)
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    # Clients may send their own model field; the configured upstream model is authoritative.
    model: str | None = None
    messages: list[Message] = Field(min_length=1, max_length=256)
    max_tokens: int = Field(default=256, ge=1, le=32768)
    temperature: float = Field(default=0.2, ge=0, le=2)


@app.get("/")
def root() -> dict[str, Any]:
    ready = bool(UPSTREAM_BASE_URL and MODEL_ID)
    return {
        "service": "ARIES AI API",
        "api_version": app.version,
        "status": "configured" if ready else "needs_backend",
        "inference_ready": ready,
        "note": (
            "Backend URL and model ID are configured; run a real chat request to verify inference."
            if ready
            else "Set ARIES_UPSTREAM_BASE_URL and ARIES_MODEL_ID; set ARIES_UPSTREAM_API_KEY if the provider requires it."
        ),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "aries-ai-api"}


@app.get("/diagnostics")
def diagnostics() -> dict[str, Any]:
    """Expose configuration presence only; never reveal secret values."""
    configured = bool(UPSTREAM_BASE_URL and MODEL_ID)
    return {
        "service": "ARIES AI API",
        "api_version": app.version,
        "checks": {
            "upstream_base_url_configured": bool(UPSTREAM_BASE_URL),
            "model_id_configured": bool(MODEL_ID),
            "api_key_configured": bool(UPSTREAM_API_KEY),
            "api_key_required_by_all_providers": False,
        },
        "inference_configured": configured,
        "next_step": (
            "Run a real chat completion to verify inference."
            if configured
            else "Add ARIES_UPSTREAM_BASE_URL and ARIES_MODEL_ID in Render Environment; add ARIES_UPSTREAM_API_KEY if the provider requires authentication."
        ),
    }


@app.get("/v1/models")
def models() -> dict[str, Any]:
    if not MODEL_ID:
        return {
            "object": "list",
            "data": [],
            "inference_ready": False,
            "note": "Set ARIES_MODEL_ID to the exact model name accepted by the configured backend.",
        }
    return {
        "object": "list",
        "data": [{"id": MODEL_ID, "object": "model", "owned_by": "aries"}],
        "inference_ready": bool(UPSTREAM_BASE_URL),
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest) -> dict[str, Any]:
    if not UPSTREAM_BASE_URL or not MODEL_ID:
        raise HTTPException(
            status_code=503,
            detail=(
                "Inference backend is not fully configured. Set ARIES_UPSTREAM_BASE_URL "
                "and ARIES_MODEL_ID to a real, authorized OpenAI-compatible model API "
                "and its exact model ID."
            ),
        )

    payload = request.model_dump(exclude={"model"})
    payload["model"] = MODEL_ID
    headers = {"Content-Type": "application/json"}
    if UPSTREAM_API_KEY:
        headers["Authorization"] = f"Bearer {UPSTREAM_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT_SECONDS) as client:
            response = await client.post(
                chat_completions_url(UPSTREAM_BASE_URL),
                json=payload,
                headers=headers,
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="The model backend timed out.")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not connect to the configured model backend.")

    if response.status_code >= 400:
        # Avoid returning upstream error bodies, which may contain private details.
        raise HTTPException(
            status_code=502,
            detail=(
                f"Model backend returned HTTP {response.status_code}. "
                "Check backend URL, model ID, and credentials."
            ),
        )
    try:
        return response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Model backend returned a non-JSON response.")
