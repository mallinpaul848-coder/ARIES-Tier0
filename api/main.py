# ARIES public gateway: real inference requires an explicitly configured upstream backend.
import os
import math
import numbers
import time
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from aries_math.chat_router import route_math_prompt
from software.native_reasoner import solve as solve_native_prompt
from aries_math.prise_research_engine import ARIESPRISEResearchEngine, PRISEProfile, PRIZE_PROBLEM_ROUTES

app = FastAPI(title="ARIES AI API", version="1.0.5")

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


class ResearchAnalysisRequest(BaseModel):
    problem: str = Field(min_length=1, max_length=160)
    values: list[float] = Field(default_factory=list, max_length=4096)
    priority: float = Field(default=1.0, ge=0.0)
    risk: float = Field(default=1.0, ge=0.0)
    impact: float = Field(default=1.0, ge=0.0)
    systemic: float = Field(default=1.0, ge=0.0)
    emergent: float = Field(default=1.0, ge=0.0)


class CalculationRequest(BaseModel):
    """Request for bounded, deterministic ARIES math operations."""
    operation: str = Field(min_length=1, max_length=64)
    parameters: dict[str, Any] = Field(default_factory=dict)


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise ValueError(f"'{name}' must be an integer.")
    return int(value)


def _integer_list(value: Any, name: str, *, maximum: int = 10000) -> list[int]:
    if not isinstance(value, list) or not value or len(value) > maximum:
        raise ValueError(f"'{name}' must be a non-empty list of at most {maximum} integers.")
    return [_integer(item, f"{name}[{index}]") for index, item in enumerate(value)]


def _matrix(value: Any, name: str) -> list[list[int]]:
    if not isinstance(value, list) or not value or len(value) > 128:
        raise ValueError(f"'{name}' must be a non-empty matrix with at most 128 rows.")
    rows = []
    width = None
    for row_index, row in enumerate(value):
        if not isinstance(row, list) or not row or len(row) > 128:
            raise ValueError(f"'{name}' rows must be non-empty lists with at most 128 columns.")
        parsed = [_integer(item, f"{name}[{row_index}][{col}]") for col, item in enumerate(row)]
        if width is None:
            width = len(parsed)
        elif len(parsed) != width:
            raise ValueError(f"'{name}' must be rectangular.")
        rows.append(parsed)
    return rows


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def execute_aries_operation(operation: str, parameters: dict[str, Any]) -> Any:
    """Run allow-listed deterministic math; never evaluate arbitrary code."""
    op = operation.strip().lower().replace("-", "_")
    if op == "digital_root":
        n = _integer(parameters.get("n"), "n")
        return 0 if n == 0 else 1 + (abs(n) - 1) % 9
    if op == "gcd":
        values = _integer_list(parameters.get("values"), "values")
        return math.gcd(*values)
    if op == "lcm":
        values = _integer_list(parameters.get("values"), "values")
        return math.lcm(*values)
    if op == "is_prime":
        n = _integer(parameters.get("n"), "n")
        return _is_prime(n)
    if op == "dot_product":
        left = _integer_list(parameters.get("left"), "left")
        right = _integer_list(parameters.get("right"), "right")
        if len(left) != len(right):
            raise ValueError("'left' and 'right' must have equal lengths.")
        return sum(a * b for a, b in zip(left, right))
    if op == "matrix_multiply":
        left = _matrix(parameters.get("left"), "left")
        right = _matrix(parameters.get("right"), "right")
        if len(left[0]) != len(right):
            raise ValueError("The number of columns in 'left' must equal rows in 'right'.")
        columns = list(zip(*right))
        return [[sum(a * b for a, b in zip(row, col)) for col in columns] for row in left]
    if op == "integer_mix":
        # A reproducible 64-bit mixing function, useful for diagnostics, not cryptography.
        n = _integer(parameters.get("n"), "n") & ((1 << 64) - 1)
        n ^= n >> 12
        n ^= (n << 25) & ((1 << 64) - 1)
        n ^= n >> 27
        return (n * 0x2545F4914F6CDD1D) & ((1 << 64) - 1)
    raise ValueError(
        "Unsupported operation. Choose: digital_root, gcd, lcm, is_prime, "
        "dot_product, matrix_multiply, integer_mix."
    )


_RESEARCH_ENGINE = ARIESPRISEResearchEngine()


@app.get("/v8/research/problems")
def v8_research_problems() -> dict[str, Any]:
    return {
        "engine": "ARIES PRISE Research Math Engine",
        "problems": [
            {"name": name, "route": list(route)}
            for name, route in sorted(PRIZE_PROBLEM_ROUTES.items())
        ],
        "operators": ["PRISE", "digital_root_369", "vortex369", "phase8", "helixo_features"],
    }


@app.post("/v8/research/analyze")
def v8_research_analyze(payload: ResearchAnalysisRequest) -> dict[str, Any]:
    profile = PRISEProfile(
        priority=payload.priority,
        risk=payload.risk,
        impact=payload.impact,
        systemic=payload.systemic,
        emergent=payload.emergent,
    )
    try:
        return _RESEARCH_ENGINE.analyze(payload.problem, payload.values, profile)
    except (ValueError, TypeError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/v8/execute/operations")
def v8_operations() -> dict[str, Any]:
    return {
        "version": "8.0",
        "mode": "deterministic_allowlisted_math",
        "operations": [
            "digital_root", "gcd", "lcm", "is_prime",
            "dot_product", "matrix_multiply", "integer_mix"
        ],
        "note": "These are deterministic mathematical operations, not a mathematical proof generator or full AI inference.",
    }


@app.post("/v8/execute")
def v8_execute(payload: CalculationRequest) -> dict[str, Any]:
    started = time.perf_counter_ns()
    try:
        result = execute_aries_operation(payload.operation, payload.parameters)
    except (ValueError, TypeError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    elapsed_ns = time.perf_counter_ns() - started
    return {
        "status": "success",
        "engine": "ARIES deterministic math",
        "version": "8.0",
        "operation": payload.operation.strip().lower().replace("-", "_"),
        "result": result,
        "elapsed_ns": elapsed_ns,
        "timing_scope": "server-side operation handler only; excludes network and model inference",
    }


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


def _deterministic_completion(answer: str, route: str) -> dict[str, Any]:
    return {
        "id": "chatcmpl-aries-" + str(time.time_ns()),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "aries-deterministic",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": answer},
            "finish_reason": "stop",
        }],
        "aries_runtime": {
            "engine": "ARIES deterministic reasoning",
            "route": route,
            "inference_seconds": 0,
            "deterministic": True,
        },
    }


def _try_deterministic_completion(request: ChatRequest) -> dict[str, Any] | None:
    latest_user = next(
        (message.content for message in reversed(request.messages) if message.role == "user"),
        None,
    )
    if not latest_user:
        return None
    try:
        routed = route_math_prompt(latest_user)
    except (ValueError, TypeError, OverflowError):
        routed = None
    if routed is not None:
        return _deterministic_completion(routed["answer"], routed["route"])
    answer = solve_native_prompt(latest_user)
    if answer is not None:
        return _deterministic_completion(answer, "native_reasoner")
    return None


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest) -> dict[str, Any]:
    deterministic = _try_deterministic_completion(request)
    if deterministic is not None:
        return deterministic
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
