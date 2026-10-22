#!/usr/bin/env python3
"""ARIES self-hosted local inference server. No external chat API is used."""
from __future__ import annotations

import json
import os
import time
import uuid
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
import threading
import webbrowser
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse

MODEL_REPO = os.getenv("ARIES_MODEL_REPO", "bartowski/Qwen2.5-1.5B-Instruct-GGUF")
MODEL_FILE = os.getenv("ARIES_MODEL_FILE", "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf")
MODEL_ID = "aries-self-hosted-qwen2.5-1.5b"
HOST = os.getenv("ARIES_HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8765"))
MODEL_LOCK = Lock()


def load_model():
    from huggingface_hub import hf_hub_download
    from llama_cpp import Llama

    local_path = os.getenv("ARIES_GGUF_MODEL_PATH", "").strip()
    if not local_path:
        local_path = hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE)
    if not Path(local_path).is_file():
        raise FileNotFoundError("Model file not found: " + local_path)
    context = max(2048, min(int(os.getenv("ARIES_CONTEXT_SIZE", "4096")), 8192))
    threads = max(1, min(int(os.getenv("ARIES_CPU_THREADS", str(os.cpu_count() or 4))), 16))
    print(f"Loading {MODEL_ID} on CPU (context={context}, threads={threads})", flush=True)
    model = Llama(
        model_path=local_path,
        n_ctx=context,
        n_threads=threads,
        n_batch=128,
        n_gpu_layers=0,
        use_mmap=True,
        verbose=False,
    )
    print("ARIES local model ready.", flush=True)
    return model


MODEL = load_model()


class Handler(BaseHTTPRequestHandler):
    server_version = "ARIES-SelfHosted/1.0"

    def send_json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            return self.send_json(200, {"status": "ok", "service": "aries-self-hosted", "inference_ready": True})
        if path == "/":
            return self.send_json(200, {
                "service": "ARIES AI Self-Hosted Inference",
                "backend": "local llama.cpp",
                "model_id": MODEL_ID,
                "general_chat_ready": True,
                "external_chat_provider": False,
            })
        if path == "/v1/models":
            return self.send_json(200, {"object": "list", "data": [{"id": MODEL_ID, "object": "model", "owned_by": "aries"}]})
        return self.send_json(404, {"error": {"message": "Not found"}})

    def do_POST(self):
        if urlparse(self.path).path != "/v1/chat/completions":
            return self.send_json(404, {"error": {"message": "Not found"}})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 1_000_000:
                return self.send_json(400, {"error": {"message": "Request body must be between 1 byte and 1 MB."}})
            body = json.loads(self.rfile.read(size))
            messages = body.get("messages")
            if not isinstance(messages, list) or not messages:
                return self.send_json(400, {"error": {"message": "messages must be a non-empty array"}})
            clean = []
            for item in messages[-32:]:
                if not isinstance(item, dict):
                    continue
                role, content = item.get("role"), item.get("content")
                if role in {"system", "user", "assistant"} and isinstance(content, str) and content.strip():
                    clean.append({"role": role, "content": content[-12000:]})
            if not any(m["role"] == "user" for m in clean):
                return self.send_json(400, {"error": {"message": "At least one user message is required"}})
            if not any(m["role"] == "system" for m in clean):
                clean.insert(0, {"role": "system", "content":
                    "You are ARIES AI in the MALLIN platform. Be capable, accurate, and direct. "
                    "Solve the actual task, reason carefully, verify calculations, provide complete "
                    "working code when asked, and use the conversation context. Do not invent sources, "
                    "facts, or actions. Clearly distinguish uncertainty from known information."})
            max_tokens = max(1, min(int(body.get("max_tokens", 768)), 2048))
            temperature = max(0.0, min(float(body.get("temperature", 0.3)), 1.5))
            started = time.perf_counter_ns()
            with MODEL_LOCK:
                result = MODEL.create_chat_completion(
                    messages=clean,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9,
                    repeat_penalty=1.08,
                )
            elapsed = time.perf_counter_ns() - started
            choices = result.get("choices", [])
            answer = choices[0].get("message", {}).get("content", "") if choices else ""
            if not isinstance(answer, str) or not answer.strip():
                return self.send_json(502, {"error": {"message": "Local model returned an empty response"}})
            return self.send_json(200, {
                "id": "chatcmpl-" + uuid.uuid4().hex,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": MODEL_ID,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": answer.strip()}, "finish_reason": "stop"}],
                "aries": {"backend": "self-hosted-local-model", "external_chat_provider": False, "inference_ns": elapsed},
                "usage": result.get("usage", {}),
            })
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.send_json(400, {"error": {"message": "Invalid request: " + str(exc)}})
        except Exception as exc:
            print("Inference request failed: " + type(exc).__name__, flush=True)
            return self.send_json(500, {"error": {"message": "Local inference failed. Check the server window."}})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


ROOT = Path(__file__).resolve().parent.parent
WEB_HOST = "127.0.0.1"
WEB_PORT = int(os.getenv("ARIES_WEB_PORT", "8081"))


class WebsiteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print("WEBSITE %s - %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    api_server = ThreadingHTTPServer((HOST, PORT), Handler)
    api_thread = threading.Thread(target=api_server.serve_forever, name="aries-api", daemon=True)
    api_thread.start()
    web_server = ThreadingHTTPServer((WEB_HOST, WEB_PORT), WebsiteHandler)
    site_url = f"http://{WEB_HOST}:{WEB_PORT}/"
    print(f"ARIES local API: http://{HOST}:{PORT}", flush=True)
    print(f"ARIES independent website: {site_url}", flush=True)
    print("Inference runs locally. No external chat API is used.", flush=True)
    try:
        webbrowser.open(site_url)
        web_server.serve_forever()
    except KeyboardInterrupt:
        print("\\nStopping ARIES website and local API...", flush=True)
    finally:
        web_server.shutdown()
        api_server.shutdown()
        web_server.server_close()
        api_server.server_close()
