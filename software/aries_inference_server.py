#!/usr/bin/env python3
"""ARIES Local Inference Server.

Runs a real local GGUF language model on the operator's computer. No OpenAI API
key or hosted inference provider is required. Install llama-cpp-python and place
a compatible GGUF model at ARIES_GGUF_MODEL_PATH (or run download_model.py).

This is an inference wrapper/runtime, not a newly trained foundation model.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

MODEL_PATH = Path(os.getenv("ARIES_GGUF_MODEL_PATH", "models/aries-model.gguf"))
MODEL_ID = os.getenv("ARIES_LOCAL_MODEL_ID", "aries-local-gguf")
HOST = os.getenv("ARIES_HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", os.getenv("ARIES_PORT", "8080")))
N_CTX = max(512, min(int(os.getenv("ARIES_CONTEXT_SIZE", "4096")), 32768))
N_THREADS = max(1, int(os.getenv("ARIES_THREADS", str(os.cpu_count() or 4))))
N_GPU_LAYERS = int(os.getenv("ARIES_GPU_LAYERS", "0"))
MODEL = None
LOAD_ERROR = None


def load_model():
    global MODEL, LOAD_ERROR
    try:
        from llama_cpp import Llama
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"GGUF model not found at {MODEL_PATH}. Run: python software/download_model.py"
            )
        MODEL = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False,
        )
        LOAD_ERROR = None
    except Exception as exc:
        LOAD_ERROR = f"{type(exc).__name__}: {exc}"


class Handler(BaseHTTPRequestHandler):
    server_version = "ARIES-Local-Inference/1.0"

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        ready = MODEL is not None
        if path in ("/", "/health", "/v1/health"):
            return self.send_json(200 if ready else 503, {
                "status": "ok" if ready else "model_not_loaded",
                "service": "ARIES Local Inference",
                "engine": "llama-cpp-python",
                "model_loaded": ready,
                "model_path_exists": MODEL_PATH.is_file(),
                "detail": LOAD_ERROR if not ready else None,
            })
        if path == "/v1/models":
            return self.send_json(200, {
                "object": "list",
                "data": ([{"id": MODEL_ID, "object": "model", "owned_by": "aries-local"}] if ready else []),
                "inference_ready": ready,
            })
        return self.send_json(404, {"error": {"message": "Not found", "type": "not_found"}})

    def do_POST(self):
        if urlparse(self.path).path != "/v1/chat/completions":
            return self.send_json(404, {"error": {"message": "Not found", "type": "not_found"}})
        if MODEL is None:
            return self.send_json(503, {
                "error": {"message": "Local model is not loaded. Check /health and the model file.", "type": "model_not_ready"},
                "detail": LOAD_ERROR,
            })
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 2_000_000:
                return self.send_json(400, {"error": {"message": "Request body must be 1 byte to 2 MB.", "type": "invalid_request_error"}})
            request = json.loads(self.rfile.read(length))
            messages = request.get("messages")
            if not isinstance(messages, list) or not messages:
                return self.send_json(400, {"error": {"message": "messages must be a non-empty array.", "type": "invalid_request_error"}})
            normalized = []
            for item in messages:
                if not isinstance(item, dict) or item.get("role") not in ("system", "user", "assistant", "tool"):
                    return self.send_json(400, {"error": {"message": "Each message needs a valid role and content.", "type": "invalid_request_error"}})
                content = item.get("content", "")
                if not isinstance(content, str):
                    return self.send_json(400, {"error": {"message": "Only text message content is supported.", "type": "invalid_request_error"}})
                normalized.append({"role": item["role"], "content": content})
            max_tokens = max(1, min(int(request.get("max_tokens", 256)), 2048))
            temperature = max(0.0, min(float(request.get("temperature", 0.7)), 2.0))
            started = time.perf_counter()
            result = MODEL.create_chat_completion(
                messages=normalized,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=max(0.01, min(float(request.get("top_p", 0.95)), 1.0)),
            )
            elapsed = time.perf_counter() - started
            choice = result["choices"][0]
            content = (choice.get("message") or {}).get("content") or ""
            if not content.strip():
                return self.send_json(502, {"error": {"message": "The local model returned empty output.", "type": "empty_model_output"}})
            result["id"] = "chatcmpl-" + uuid.uuid4().hex
            result["model"] = MODEL_ID
            result["aries_runtime"] = {
                "engine": "llama-cpp-python",
                "inference_seconds": round(elapsed, 6),
                "model_file": MODEL_PATH.name,
                "local_inference": True,
            }
            return self.send_json(200, result)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.send_json(400, {"error": {"message": str(exc), "type": "invalid_request_error"}})
        except Exception as exc:
            return self.send_json(500, {"error": {"message": f"Local inference failed: {type(exc).__name__}", "type": "inference_error"}})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    load_model()
    if MODEL is None:
        print("ARIES local inference did not load:", LOAD_ERROR, flush=True)
        print("The server will still start so /health explains the missing dependency/model.", flush=True)
    else:
        print(f"ARIES local model loaded: {MODEL_PATH} (ctx={N_CTX}, threads={N_THREADS})", flush=True)
    print(f"ARIES inference API: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
