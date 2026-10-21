"""OpenAI-compatible upstream chat client for ARIES."""
from __future__ import annotations

import json
import os
import time
from urllib import error, request
from urllib.parse import urlsplit


class UpstreamInferenceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def chat_completions_url(base_url: str) -> str:
    """Normalize a provider root, /v1 base, or full completions URL."""
    normalized = str(base_url).strip().rstrip("/")
    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("ARIES_UPSTREAM_BASE_URL must be a valid HTTP(S) URL.")
    if parsed.path.rstrip("/").endswith("/chat/completions"):
        return normalized
    if parsed.path.rstrip("/").endswith("/v1"):
        return normalized + "/chat/completions"
    return normalized + "/v1/chat/completions"


def upstream_configuration() -> tuple[str, str, str]:
    """Read upstream configuration without logging or returning it to clients."""
    base_url = os.getenv("ARIES_UPSTREAM_BASE_URL", "").strip().rstrip("/")
    model_id = os.getenv("ARIES_MODEL_ID", "").strip()
    api_key = (
        os.getenv("ARIES_UPSTREAM_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
    )
    return base_url, model_id, api_key


def request_upstream_answer(
    messages: list[dict],
    *,
    base_url: str,
    model_id: str,
    api_key: str = "",
    max_tokens: int = 256,
    temperature: float = 0.2,
    timeout_seconds: float = 90.0,
) -> tuple[str, int]:
    """Return assistant text and measured round-trip nanoseconds."""
    if not base_url or not model_id:
        raise UpstreamInferenceError(
            "General chat is not configured. Set ARIES_UPSTREAM_BASE_URL and ARIES_MODEL_ID.",
            503,
        )

    valid_messages: list[dict[str, str]] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in {"system", "user", "assistant"} or not isinstance(content, str):
            continue
        if content.strip():
            valid_messages.append({"role": role, "content": content})

    if not any(item["role"] == "user" for item in valid_messages):
        raise UpstreamInferenceError("At least one non-empty user message is required.", 400)

    if not any(item["role"] == "system" for item in valid_messages):
        valid_messages.insert(0, {
            "role": "system",
            "content": (
                "You are ARIES AI in the MALLIN platform. Answer the user's actual "
                "question directly, follow requested formats, show calculations when "
                "useful, and do not invent facts when uncertain."
            ),
        })

    payload = {
        "model": model_id,
        "messages": valid_messages[-64:],
        "max_tokens": max(1, min(int(max_tokens), 4096)),
        "temperature": max(0.0, min(float(temperature), 2.0)),
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = "Bearer " + api_key

    req = request.Request(
        chat_completions_url(base_url),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    started_ns = time.perf_counter_ns()
    try:
        with request.urlopen(req, timeout=max(1.0, min(float(timeout_seconds), 300.0))) as response:
            raw = response.read(4_000_000).decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        code = 504 if exc.code == 504 else 502
        raise UpstreamInferenceError(
            f"The configured model provider returned HTTP {exc.code}. Check the backend URL, model ID, and credentials.",
            code,
        ) from None
    except (TimeoutError, error.URLError) as exc:
        if isinstance(exc, TimeoutError) or isinstance(getattr(exc, "reason", None), TimeoutError):
            raise UpstreamInferenceError("The model provider timed out. Try again.", 504) from None
        raise UpstreamInferenceError("ARIES could not connect to the configured model provider.", 502) from None
    except OSError:
        raise UpstreamInferenceError("ARIES could not connect to the configured model provider.", 502) from None

    elapsed_ns = max(1, time.perf_counter_ns() - started_ns)
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        raise UpstreamInferenceError("The configured model provider returned invalid JSON.", 502) from None

    choices = data.get("choices") if isinstance(data, dict) else None
    first = choices[0] if isinstance(choices, list) and choices else None
    message = first.get("message") if isinstance(first, dict) else None
    answer = message.get("content") if isinstance(message, dict) else None
    if not isinstance(answer, str) or not answer.strip():
        raise UpstreamInferenceError("The configured model provider returned an empty answer.", 502)
    return answer.strip(), elapsed_ns
