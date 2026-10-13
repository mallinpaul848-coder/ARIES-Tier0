import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="ARIES AI API", version="1.0.1")
MODEL_ID = os.getenv("ARIES_MODEL_ID", "").strip()
UPSTREAM_BASE_URL = os.getenv("ARIES_UPSTREAM_BASE_URL", "").rstrip("/")
UPSTREAM_API_KEY = os.getenv("ARIES_UPSTREAM_API_KEY", "").strip()
UPSTREAM_TIMEOUT_SECONDS = float(os.getenv("ARIES_UPSTREAM_TIMEOUT_SECONDS", "90"))


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
    ready = bool(UPSTREAM_BASE_URL)
    return {
        "service": "ARIES AI API",
        "api_version": "1.0.1",
        "status": "configured" if ready else "needs_backend",
        "inference_ready": ready,
        "note": (
            "A real OpenAI-compatible inference backend is configured."
            if ready else
            "Configure ARIES_UPSTREAM_BASE_URL and, if required, ARIES_UPSTREAM_API_KEY."
        ),
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "aries-ai-api"}


@app.get("/v1/models")
def models():
    if not MODEL_ID:
        return {
            "object": "list",
            "data": [],
            "inference_ready": bool(UPSTREAM_BASE_URL),
            "note": "Set ARIES_MODEL_ID to the model name accepted by the configured backend.",
        }
    return {
        "object": "list",
        "data": [{"id": MODEL_ID, "object": "model", "owned_by": "aries"}],
        "inference_ready": bool(UPSTREAM_BASE_URL),
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    if not UPSTREAM_BASE_URL:
        raise HTTPException(
            status_code=503,
            detail="Inference backend is not configured. Set ARIES_UPSTREAM_BASE_URL to a real, authorized OpenAI-compatible model API.",
        )

    payload = request.model_dump()
    if MODEL_ID:
        payload["model"] = MODEL_ID
    headers = {"Content-Type": "application/json"}
    if UPSTREAM_API_KEY:
        headers["Authorization"] = f"Bearer {UPSTREAM_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{UPSTREAM_BASE_URL}/v1/chat/completions",
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
