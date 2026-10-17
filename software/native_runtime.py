#!/usr/bin/env python3
"""
ARIES Native Runtime — local-first chat API.

The character n-gram model is an experimental text baseline, not a modern LLM.
For supported tasks, use explicit deterministic answers first so the baseline
does not produce misleading fragments for simple questions.
"""
import argparse
import collections
import json
import math
import os
import random
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

try:
    from native_reasoner import solve as solve_reasoner
except ImportError:
    solve_reasoner = None

DEFAULT_MODEL = "aries-native-ngram.json"
DEFAULT_CORPUS = "data/training.txt"
ORDER = 5


def answer_known_question(prompt):
    """Return a concise answer only for simple, explicit, verifiable prompts."""
    text = " ".join(str(prompt).strip().split())
    lower = text.lower().strip(" .?!")
    if re.search(r"\bhow many counties (?:are there )?in texas\b", lower):
        return "Texas has 254 counties."
    if re.search(r"\b(?:what'?s|what is) (?:your|ur) name\b", lower) or lower in {
        "who are you", "what is your name", "whats your name"
    }:
        return "My name is ARIES. I'm an experimental AI system. My local baseline has limited capabilities, so I will say when I cannot answer reliably."
    if lower in {"what is 2 + 2", "what's 2 + 2", "what is 2 plus 2"}:
        return "4"
    if solve_reasoner:
        try:
            result = solve_reasoner(text)
            if isinstance(result, str) and result.strip():
                return result.strip()
        except (ValueError, TypeError, ArithmeticError):
            pass
    return None


def train(corpus_path, model_path, order=ORDER):
    path = Path(corpus_path)
    if not path.exists():
        raise SystemExit(
            f"Training corpus not found: {path}\n"
            "Create a UTF-8 text file with example text, one or more paragraphs, then train again."
        )
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text.strip()) < 100:
        raise SystemExit("Training text is too small; provide at least 100 non-whitespace characters.")
    text = text.replace("\r\n", "\n")
    counts = collections.defaultdict(collections.Counter)
    padded = ("\u0002" * order) + text + "\u0003"
    for i in range(order, len(padded)):
        for n in range(order + 1):
            context = padded[i-n:i] if n else ""
            counts[context][padded[i]] += 1
    serial = {ctx: dict(counter) for ctx, counter in counts.items()}
    payload = {
        "format": "aries-native-char-ngram-v1",
        "order": order,
        "trained_characters": len(text),
        "contexts": serial,
        "description": "Operator-corpus-trained character n-gram baseline; not a pretrained LLM."
    }
    Path(model_path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "trained", "model": str(model_path), "characters": len(text),
                      "contexts": len(serial), "order": order}, indent=2))


class NativeModel:
    def __init__(self, model_path):
        raw = json.loads(Path(model_path).read_text(encoding="utf-8"))
        if raw.get("format") != "aries-native-char-ngram-v1":
            raise ValueError("Unsupported ARIES native model format")
        self.order = int(raw["order"])
        self.counts = {ctx: collections.Counter(items) for ctx, items in raw["contexts"].items()}
        self.vocab = sorted({ch for counter in self.counts.values() for ch in counter})
        if not self.vocab:
            raise ValueError("Model has no vocabulary")
        self.trained_characters = int(raw.get("trained_characters", 0))

    def generate(self, prompt, max_tokens=240, temperature=0.7):
        rng = random.Random()
        out = str(prompt)
        context = ("\u0002" * self.order + out)[-self.order:]
        temperature = max(0.05, min(float(temperature), 2.0))
        for _ in range(max(1, min(int(max_tokens), 4000))):
            counter = None
            for n in range(self.order, -1, -1):
                key = context[-n:] if n else ""
                counter = self.counts.get(key)
                if counter:
                    break
            if not counter:
                break
            chars = list(counter.keys())
            weights = [count ** (1.0 / temperature) for count in counter.values()]
            next_char = rng.choices(chars, weights=weights, k=1)[0]
            if next_char == "\u0003":
                break
            out += next_char
            context = (context + next_char)[-self.order:]
        return out[len(str(prompt)):]


def make_handler(model):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ARIES-Native/1.1"

        def _send(self, status, obj):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
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
            if path in ("/", "/health", "/v1/models"):
                if path == "/v1/models":
                    return self._send(200, {"object":"list","data":[{"id":"aries-native","object":"model","owned_by":"aries"}]})
                return self._send(200, {"status":"ok","service":"ARIES Native Runtime",
                    "model_format":"character n-gram baseline with deterministic task rules",
                    "trained_characters":model.trained_characters,"inference_ready":True,
                    "note":"Experimental baseline, not a modern LLM."})
            return self._send(404, {"error":"not_found"})

        def do_POST(self):
            if urlparse(self.path).path != "/v1/chat/completions":
                return self._send(404, {"error":"not_found"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > 1_000_000:
                    return self._send(400, {"error":"invalid_request","detail":"Request body must be 1 byte to 1 MB."})
                body = json.loads(self.rfile.read(size))
                messages = body.get("messages", [])
                if not isinstance(messages, list) or not messages:
                    return self._send(400, {"error":"invalid_request","detail":"messages must be a non-empty list"})
                prompt = "\n".join(str(m.get("content", "")) for m in messages if isinstance(m, dict))
                max_tokens = min(int(body.get("max_tokens", 240)), 1000)
                temperature = float(body.get("temperature", 0.7))
                start = time.perf_counter()
                completion = answer_known_question(prompt)
                if completion is None:
                    # Do not present random n-gram fragments as reliable factual answers.
                    completion = ("I don't have a reliable answer to that question in this experimental local baseline. "
                                  "The current engine is a small character n-gram model, not a general-purpose LLM. "
                                  "Connect a capable model backend or add a tested rule for this task.")
                elapsed = time.perf_counter() - start
                return self._send(200, {"id":"aries-native-local","object":"chat.completion",
                    "created":int(time.time()),"model":"aries-native",
                    "choices":[{"index":0,"message":{"role":"assistant","content":completion},
                                "finish_reason":"stop"}],
                    "usage":{"prompt_tokens":len(prompt),"completion_tokens":len(completion),
                             "total_tokens":len(prompt)+len(completion)},
                    "aries_native":{"inference_seconds":round(elapsed,6),"runtime":"stdlib-ngram+rules"}})
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                return self._send(400, {"error":"invalid_request","detail":str(exc)})

        def log_message(self, fmt, *args):
            print("%s - %s" % (self.address_string(), fmt % args))
    return Handler


def main():
    p = argparse.ArgumentParser(description="ARIES standalone local text model")
    sub = p.add_subparsers(dest="command", required=True)
    t = sub.add_parser("train", help="Train a tiny character n-gram model from local text")
    t.add_argument("--corpus", default=DEFAULT_CORPUS)
    t.add_argument("--model", default=DEFAULT_MODEL)
    t.add_argument("--order", type=int, default=ORDER, choices=range(2, 9))
    s = sub.add_parser("serve", help="Serve local inference via OpenAI-compatible HTTP API")
    s.add_argument("--model", default=DEFAULT_MODEL)
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    args = p.parse_args()
    if args.command == "train":
        train(args.corpus, args.model, args.order)
    else:
        model = NativeModel(args.model)
        server = ThreadingHTTPServer((args.host, args.port), make_handler(model))
        print(f"ARIES Native Runtime listening at http://{args.host}:{args.port}")
        print("Routes: GET /health, GET /v1/models, POST /v1/chat/completions")
        print("Experimental baseline, not a modern LLM.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping ARIES Native Runtime.")
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
