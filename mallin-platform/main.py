import os
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
import httpx

app = FastAPI(title="MALLIN Platform", version="0.1.0")
TOKEN = os.environ.get("MALLIN_ADMIN_TOKEN", "")
ARIES = os.environ.get("ARIES_API_URL", "https://aries-tier0-api-6qjh.onrender.com").rstrip("/")
STATIC = Path(__file__).parent / "static"

@app.get("/health")
async def health():
    return {"status": "ok", "service": "mallin-platform"}

@app.get("/api/status")
async def status():
    result = {"platform": "operational", "aries_api": "unknown", "aries_url": ARIES}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(f"{ARIES}/health")
            result["aries_api"] = "online" if response.is_success else "degraded"
            result["aries_http_status"] = response.status_code
    except httpx.HTTPError:
        result["aries_api"] = "offline"
    return result

@app.post("/api/admin/check")
async def admin_check(authorization: str | None = Header(default=None)):
    if not TOKEN or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"authorized": True, "platform": "mallin-platform"}

@app.post("/v1/chat/completions")
async def chat(request: Request):
    body = await request.json()
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(f"{ARIES}/v1/chat/completions", json=body)
        return JSONResponse(status_code=response.status_code, content=response.json())
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"ARIES backend unavailable: {exc.__class__.__name__}")

@app.get("/")
async def homepage():
    return FileResponse(STATIC / "index.html")
