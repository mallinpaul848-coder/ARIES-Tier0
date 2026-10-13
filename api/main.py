import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="ARIES AI API", version="1.0.0")
MODEL_ID = os.getenv("ARIES_MODEL_ID", "")
UPSTREAM_BASE_URL = os.getenv("ARIES_UPSTREAM_BASE_URL", "").rstrip("/")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "aries"
    messages: list[Message]
    max_tokens: int = 256
    temperature: float = 0.2

@app.get("/")
def root():
    return {
        "service": "ARIES AI API",
        "api_version": "1.0.0",
        "status": "scaffold",
        "inference_ready": bool(UPSTREAM_BASE_URL),
        "note": "A live model backend must be configured before chat inference is available."
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "aries-ai-api"}

@app.get("/v1/models")
def models():
    if not MODEL_ID:
        return {"object": "list", "data": [], "inference_ready": False,
                "note": "Set ARIES_MODEL_ID and configure a real inference backend."}
    return {"object": "list", "data": [{"id": MODEL_ID, "object": "model", "owned_by": "aries"}],
            "inference_ready": bool(UPSTREAM_BASE_URL)}

@app.post("/v1/chat/completions")
def chat_completions(request: ChatRequest):
    # Deliberately do not fabricate model output. Wire a real inference provider here.
    if not UPSTREAM_BASE_URL:
        raise HTTPException(
            status_code=503,
            detail="Inference backend is not configured. Set ARIES_UPSTREAM_BASE_URL to a real, authorized model API."
        )
    raise HTTPException(
        status_code=501,
        detail="Upstream adapter is not implemented yet; no model response has been generated."
    )
