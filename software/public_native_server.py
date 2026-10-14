#!/usr/bin/env python3
"""ARIES-owned public HTTP gateway for its native character n-gram baseline."""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from native_runtime import NativeModel
from native_reasoner import solve

MODEL_PATH = os.getenv("ARIES_NATIVE_MODEL", "/app/models/aries-native-ngram.json")
MODEL = NativeModel(MODEL_PATH)
MODEL_ID = "aries-native-ngram"
PORT = int(os.getenv("PORT", "10000"))
HOST = "0.0.0.0"

class Handler(BaseHTTPRequestHandler):
    server_version = "ARIES-Native-Gateway/1.0"
    def send_json(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
    def do_GET(self):
        path = urlparse(self.path).path
        ready = True
        if path == "/health":
            return self.send_json(200, {"status":"ok","service":"aries-ai-api"})
        if path == "/":
            return self.send_json(200, {
                "service":"ARIES AI API","api_version":"1.0.6",
                "status":"configured","inference_ready":ready,
                "backend":"aries-native-char-ngram",
                "model_id":MODEL_ID,"native_reasoner_enabled":True,"native_reasoner_version":"0.2",
                "note":"Standalone ARIES-owned character n-gram baseline. Functional inference is available; this is not a modern LLM."
            })
        if path == "/diagnostics":
            return self.send_json(200, {
                "service":"ARIES AI API","api_version":"1.0.6",
                "native_reasoner_version":"0.2",
                "checks":{"upstream_base_url_configured":False,"model_id_configured":True,
                          "api_key_configured":False,"native_model_loaded":True,"deterministic_reasoner_loaded":True},
                "inference_configured":True,"backend":"native",
                "model_format":"hybrid deterministic task engine plus character n-gram baseline",
                "trained_characters":MODEL.trained_characters,
                "next_step":"Run real response-quality tests; this baseline is not a modern LLM."
            })
        if path == "/v1/models":
            return self.send_json(200, {"object":"list","data":[
                {"id":MODEL_ID,"object":"model","owned_by":"aries"}],
                "inference_ready":True,"model_type":"character n-gram baseline"})
        return self.send_json(404, {"error":{"message":"Not found","type":"not_found"}})
    def do_POST(self):
        if urlparse(self.path).path != "/v1/chat/completions":
            return self.send_json(404, {"error":{"message":"Not found","type":"not_found"}})
        try:
            size = int(self.headers.get("Content-Length","0"))
            if size <= 0 or size > 1_000_000:
                return self.send_json(400, {"error":{"message":"Request body must be 1 byte to 1 MB."}})
            body = json.loads(self.rfile.read(size))
            messages = body.get("messages")
            if not isinstance(messages,list) or not messages:
                return self.send_json(400, {"error":{"message":"messages must be a non-empty list"}})
            prompt = "\n".join(str(m.get("content","")) for m in messages if isinstance(m,dict))
            if not prompt.strip():
                return self.send_json(400, {"error":{"message":"message content must not be empty"}})
            max_tokens = max(1,min(int(body.get("max_tokens",128)),512))
            temperature = max(0.05,min(float(body.get("temperature",0.7)),2.0))
            started = time.perf_counter()
            answer = solve(prompt)
            if answer is None:
                answer = MODEL.generate(prompt, max_tokens=max_tokens, temperature=temperature)
            elapsed = time.perf_counter()-started
            if not answer.strip():
                answer = "ARIES native n-gram inference ran but produced no text for this prompt. This baseline has limited capability."
            return self.send_json(200, {
                "id":"chatcmpl-aries-native","object":"chat.completion",
                "created":int(time.time()),"model":MODEL_ID,
                "choices":[{"index":0,"message":{"role":"assistant","content":answer},
                            "finish_reason":"stop"}],
                "usage":{"prompt_tokens":len(prompt),"completion_tokens":len(answer),
                         "total_tokens":len(prompt)+len(answer)},
                "aries_native":{"runtime":"stdlib-char-ngram","inference_seconds":round(elapsed,6),
                                "model_type":"baseline_not_modern_llm"}
            })
        except (ValueError,TypeError,json.JSONDecodeError) as exc:
            return self.send_json(400, {"error":{"message":"Invalid request: "+str(exc)}})
    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

if __name__ == "__main__":
    print(f"ARIES native gateway listening on {HOST}:{PORT}; model={MODEL_ID}; chars={MODEL.trained_characters}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
