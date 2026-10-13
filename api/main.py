import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="ARIES AI API", version="1.0.3")
MODEL_ID = os.getenv("ARIES_MODEL_ID", "").strip()
UPSTREAM_BASE_URL = os.getenv("ARIES_UPSTREAM_BASE_URL", "").rstrip("/")
UPSTREAM_API_KEY = os.getenv("ARIES_UPSTREAM_API_KEY", "").strip()
UPSTREAM_TIMEOUT_SECONDS = float(os.getenv("ARIES_UPSTREAM_TIMEOUT_SECONDS", "90"))


def chat_completions_url(base_url: str) -> str:
    """Build the chat endpoint for providers whose base URL may already end in /v1."""
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return f"{normalized}/chat/completions"
    return f"{normalized}/v1/chat/completions"


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "aries"
    messages: list[Message] = Field(min_length=1)
    max_tokens: int = Field(default=256, ge=1, le=32768)
    temperature: float = Field(default=0.2, ge=0, le=2)


@app.get("/")
def root():
    ready = bool(UPSTREAM_BASE_URL and MODEL_ID)
    return {
        "service": "ARIES AI API",
        "api_version": "1.0.2",
        "status": "configured" if ready else "needs_backend",
        "inference_ready": ready,
        "note": (
            "Backend URL and model ID are configured; run a real chat request to verify inference."
            if ready else
            "Set ARIES_UPSTREAM_BASE_URL and ARIES_MODEL_ID; set ARIES_UPSTREAM_API_KEY if the provider requires it."
        ),
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "aries-ai-api"}


@app.get("/diagnostics")
def diagnostics():
    """Expose configuration presence only; never reveal secret values."""
    return {
        "service": "ARIES AI API",
        "api_version": app.version,
        "checks": {
            "upstream_base_url_configured": bool(UPSTREAM_BASE_URL),
            "model_id_configured": bool(MODEL_ID),
            "api_key_configured": bool(UPSTREAM_API_KEY),
            "api_key_required_by_all_providers": False,
        },
        "inference_configured": bool(UPSTREAM_BASE_URL and MODEL_ID),
        "next_step": (
            "Run a real chat completion to verify inference."
            if UPSTREAM_BASE_URL and MODEL_ID
            else "Add ARIES_UPSTREAM_BASE_URL and ARIES_MODEL_ID in Render Environment; add ARIES_UPSTREAM_API_KEY if the provider requires authentication."
        ),
    }


@app.get("/v1/models")
def models():
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
async def chat_completions(request: ChatRequest):
    if not UPSTREAM_BASE_URL or not MODEL_ID:
        raise HTTPException(
            status_code=503,
            detail="Inference backend is not fully configured. Set ARIES_UPSTREAM_BASE_URL and ARIES_MODEL_ID to a real, authorized OpenAI-compatible model API and its exact model ID.",
        )

    payload = request.model_dump()
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
        # Do not expose upstream response bodies, which can contain sensitive details.
        raise HTTPException(
            status_code=502,
            detail=f"Model backend returned HTTP {response.status_code}. Check backend URL, model ID, and credentials.",
        )
    try:
        return response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Model backend returned a non-JSON response.")
