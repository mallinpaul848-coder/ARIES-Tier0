#!/usr/bin/env python3
"""ARIES Unified Runtime: existing ARIES rules + FastAPI + async latency benchmark.

Run from repository root:
  python software/aries_unified.py
  python software/aries_unified.py --bench   # tests an already-running API

This integrates ARIES's existing deterministic reasoner. It does not claim to
be a newly trained large language model; unsupported prompts get an honest
fallback rather than fabricated reasoning.
"""
from __future__ import annotations
import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path
from typing import Any
import httpx
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from native_reasoner import solve as solve_reasoner
from native_runtime import answer_known_question

VERSION = "9.0.0-unified"
MODEL_ID = "aries-native"
DEFAULT_URL = "http://127.0.0.1:8000/v1/chat/completions"
app = FastAPI(title="ARIES Unified Low-Latency Platform", version=VERSION)
_started = time.perf_counter()
_request_count = 0
_latency_ms: list[float] = []

class ChatMessage(BaseModel):
    role: str = Field(min_length=1, max_length=40)
    content: str = Field(min_length=1, max_length=100_000)

class CompletionRequest(BaseModel):
    model: str = MODEL_ID
    messages: list[ChatMessage] = Field(min_length=1, max_length=256)
    max_tokens: int = Field(default=24, ge=1, le=4000)
    temperature: float = Field(default=0.2, ge=0, le=2)

def answer_prompt(prompt: str) -> tuple[str, str]:
    """Use existing auditable ARIES rules; do not fabricate model inference."""
    result = solve_reasoner(prompt)
    if isinstance(result, str) and result.strip():
        return result.strip(), "native_reasoner"
    result = answer_known_question(prompt)
    if isinstance(result, str) and result.strip():
        return result.strip(), "verified_rule"
    return (
        "I don't have a reliable answer to that question in this experimental "
        "ARIES baseline. It uses deterministic rules and a small character "
        "n-gram baseline, not a general-purpose large language model.",
        "honest_fallback",
    )

@app.get("/")
@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok", "service": "ARIES Unified Runtime", "version": VERSION,
        "model": MODEL_ID,
        "engine": "existing ARIES deterministic reasoner + verified rules",
        "uptime_seconds": round(time.perf_counter() - _started, 3),
    }

@app.get("/v1/models")
def models() -> dict[str, Any]:
    return {"object": "list", "data": [{"id": MODEL_ID, "object": "model", "owned_by": "aries"}]}

@app.get("/performance")
def performance() -> dict[str, Any]:
    samples = sorted(_latency_ms)
    def percentile(p: float) -> float | None:
        return round(samples[min(len(samples)-1, int((p/100)*len(samples)))], 3) if samples else None
    return {
        "version": VERSION, "requests_measured": _request_count,
        "latency_ms": {
            "min": round(samples[0], 3) if samples else None,
            "mean": round(statistics.mean(samples), 3) if samples else None,
            "p50": round(statistics.median(samples), 3) if samples else None,
            "p95": percentile(95), "p99": percentile(99),
            "max": round(samples[-1], 3) if samples else None,
        },
        "notice": "Measured API handling time only; no sub-nanosecond guarantee.",
    }

@app.post("/v1/chat/completions")
def chat_completions(payload: CompletionRequest) -> dict[str, Any]:
    global _request_count
    started = time.perf_counter()
    prompt = "\n".join(message.content for message in payload.messages)
    content, route = answer_prompt(prompt)
    elapsed_ms = (time.perf_counter() - started) * 1000
    _request_count += 1
    _latency_ms.append(elapsed_ms)
    if len(_latency_ms) > 10_000:
        del _latency_ms[:len(_latency_ms)-10_000]
    now = int(time.time())
    return {
        "id": f"aries-unified-{now}-{_request_count}", "object": "chat.completion",
        "created": now, "model": payload.model or MODEL_ID,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens": len(prompt.split()), "completion_tokens": len(content.split()),
            "total_tokens": len(prompt.split()) + len(content.split()),
        },
        "aries": {"version": VERSION, "route": route, "execution_latency_ms": round(elapsed_ms, 3)},
    }

async def run_benchmark(base_url: str = DEFAULT_URL, total_requests: int = 1000,
                        concurrency: int = 100, output: str = "aries_unified_report.json") -> dict[str, Any]:
    payload = {"model": MODEL_ID, "messages": [{"role": "user", "content": "What is 2 + 2?"}], "max_tokens": 24}
    concurrency = max(1, min(concurrency, 500))
    semaphore = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency)
    samples: list[float] = []
    errors: list[dict[str, Any]] = []
    started_all = time.perf_counter()
    async with httpx.AsyncClient(limits=limits) as client:
        async def send_one(index: int) -> None:
            async with semaphore:
                started = time.perf_counter()
                try:
                    response = await client.post(base_url, json=payload, timeout=15.0)
                    elapsed = (time.perf_counter() - started) * 1000
                    if response.status_code != 200:
                        errors.append({"request": index + 1, "error": f"HTTP {response.status_code}"})
                        return
                    body = response.json()
                    choices = body.get("choices")
                    if not choices or not isinstance(choices[0].get("message", {}).get("content"), str):
                        errors.append({"request": index + 1, "error": "missing assistant message"})
                        return
                    samples.append(elapsed)
                except Exception as exc:
                    errors.append({"request": index + 1, "error": str(exc)[:250]})
        await asyncio.gather(*(send_one(i) for i in range(total_requests)))
    elapsed_seconds = time.perf_counter() - started_all
    ordered = sorted(samples)
    def percentile(p: float) -> float | None:
        return round(ordered[min(len(ordered)-1, int((p/100)*len(ordered)))], 3) if ordered else None
    report = {
        "benchmark": "ARIES Unified HTTP chat latency", "version": VERSION, "target": base_url,
        "requests_requested": total_requests, "successful_responses": len(samples), "errors": len(errors),
        "latency_ms": {
            "min": round(ordered[0], 3) if ordered else None,
            "mean": round(statistics.mean(ordered), 3) if ordered else None,
            "median_p50": round(statistics.median(ordered), 3) if ordered else None,
            "p95": percentile(95), "p99": percentile(99),
            "max": round(ordered[-1], 3) if ordered else None,
        },
        "elapsed_seconds": round(elapsed_seconds, 3),
        "throughput_requests_per_second": round(len(samples)/elapsed_seconds, 2) if elapsed_seconds else None,
        "errors_sample": errors[:20],
        "limitations": "Measures HTTP latency for ARIES deterministic rules on this machine; not large-LLM quality or sub-nanosecond end-to-end inference.",
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Report saved: {path}")
    if not samples or len(errors) > max(1, int(total_requests * 0.01)):
        raise SystemExit("Benchmark failed: no valid responses or error rate above 1%.")
    return report

def main() -> None:
    parser = argparse.ArgumentParser(description="ARIES Unified Runtime")
    parser.add_argument("--bench", action="store_true", help="Benchmark an already-running API")
    parser.add_argument("--url", default=DEFAULT_URL, help="Chat completions URL for benchmark")
    parser.add_argument("--requests", type=int, default=1000, help="Benchmark request count (1–10000)")
    parser.add_argument("--concurrency", type=int, default=100, help="Concurrent requests (1–500)")
    parser.add_argument("--output", default="aries_unified_report.json", help="JSON report output path")
    parser.add_argument("--host", default="127.0.0.1", help="API bind host")
    parser.add_argument("--port", type=int, default=8000, help="API bind port")
    args = parser.parse_args()
    if args.bench:
        asyncio.run(run_benchmark(args.url, max(1, min(args.requests, 10_000)),
                                  max(1, min(args.concurrency, 500)), args.output))
    else:
        print(f"Starting ARIES Unified Runtime {VERSION} at http://{args.host}:{args.port}")
        print("Health: /health | Chat: /v1/chat/completions | Metrics: /performance")
        uvicorn.run(app, host=args.host, port=args.port, log_level="warning")

if __name__ == "__main__":
    main()
