#!/usr/bin/env python3
"""ARIES-owned public HTTP gateway for its native character n-gram baseline."""
import json
import os
from pathlib import Path
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from native_runtime import NativeModel, answer_known_question
from native_reasoner import solve
from latency_engine import FastPathEngine, LatencyMonitor
from upstream_backend import UpstreamInferenceError, request_upstream_answer, upstream_configuration
from local_model import LocalChatModel, LocalInferenceError
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aries_math.prise_unified import (ARIESExecutionEngine, PRISEProblem, exact_sat_bruteforce)
from aries_math.chat_router import route_math_prompt
from aries_math.reasoning_integration import analyze_request, build_reasoning_context

MATH_ENGINE = ARIESExecutionEngine()

MODEL_PATH = os.getenv("ARIES_NATIVE_MODEL", "/app/models/aries-native-ngram.json")
MODEL = NativeModel(MODEL_PATH)
NATIVE_MODEL_ID = "aries-native-ngram"
UPSTREAM_BASE_URL, UPSTREAM_MODEL_ID, UPSTREAM_API_KEY = upstream_configuration()
# Independent mode is the default: ARIES never sends prompts to an external AI provider.
# Set ARIES_INDEPENDENT_MODE=0 only when an operator deliberately opts into an upstream.
INDEPENDENT_MODE = os.getenv("ARIES_INDEPENDENT_MODE", "1").strip().lower() not in {"0", "false", "no", "off"}
try:
    UPSTREAM_TIMEOUT_SECONDS = max(1.0, min(float(os.getenv("ARIES_UPSTREAM_TIMEOUT_SECONDS", "90")), 300.0))
except ValueError:
    UPSTREAM_TIMEOUT_SECONDS = 90.0
UPSTREAM_READY = (not INDEPENDENT_MODE) and bool(UPSTREAM_BASE_URL and UPSTREAM_MODEL_ID)
try:
    LOCAL_MODEL = LocalChatModel()
except Exception as exc:
    print("ARIES local model unavailable: " + type(exc).__name__, flush=True)
    LOCAL_MODEL = None
LOCAL_MODEL_READY = LOCAL_MODEL is not None
MODEL_ID = (
    UPSTREAM_MODEL_ID if UPSTREAM_READY
    else "aries-local-smollm2-360m" if LOCAL_MODEL_READY
    else NATIVE_MODEL_ID
)
FAST_PATH = FastPathEngine(solve, max_entries=int(os.getenv("ARIES_FAST_CACHE_SIZE", "2048")))
LATENCY_MONITOR = LatencyMonitor(window_size=int(os.getenv("ARIES_LATENCY_WINDOW_SIZE", "2048")))
PORT = int(os.getenv("PORT", "10000"))
HOST = "0.0.0.0"

class Handler(BaseHTTPRequestHandler):
    server_version = "ARIES-Native-Gateway/1.0.10"
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
    def send_html(self, path):
        page = Path(os.getenv("ARIES_WEB_ROOT", "/app/public")) / "index.html"
        try:
            body = page.read_bytes()
        except OSError:
            return self.send_json(503, {"error": "MALLIN web interface is not installed."})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
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
        ready = UPSTREAM_READY or LOCAL_MODEL_READY
        if path in ("/app", "/app/"):
            return self.send_html(path)
        if path == "/health":
            return self.send_json(200, {"status":"ok","service":"aries-ai-api"})
        if path == "/":
            return self.send_json(200, {
                "service":"ARIES AI API","api_version":"1.0.10",
                "status":"configured","inference_ready":ready,
                "backend":"local-llama-cpp" if LOCAL_MODEL_READY else ("openai-compatible-upstream" if UPSTREAM_READY else "aries-native-char-ngram"),
                "model_id":MODEL_ID,"native_reasoner_enabled":True,"native_reasoner_version":"0.2",
                "independent_mode":INDEPENDENT_MODE,
                "general_chat_upstream_configured":UPSTREAM_READY,
                "general_chat_ready":UPSTREAM_READY or LOCAL_MODEL_READY,
                "local_model_loaded":LOCAL_MODEL_READY,
                "note":"Independent mode is local-only; general chat uses the installed local model and built-in deterministic routes remain available."
            })
        if path == "/diagnostics":
            return self.send_json(200, {
                "service":"ARIES AI API","api_version":"1.0.10",
                "native_reasoner_version":"0.2",
                "checks":{"upstream_base_url_configured":bool(UPSTREAM_BASE_URL),
                          "model_id_configured":bool(UPSTREAM_MODEL_ID or NATIVE_MODEL_ID),
                          "api_key_configured":bool(UPSTREAM_API_KEY),
                          "native_model_loaded":True,"deterministic_reasoner_loaded":True,
                          "local_model_loaded":LOCAL_MODEL_READY},
                "inference_configured":True,
                "independent_mode":INDEPENDENT_MODE,
                "backend":"local-llama-cpp" if LOCAL_MODEL_READY else ("native" if INDEPENDENT_MODE else "openai-compatible-upstream"),
                "general_chat_ready":UPSTREAM_READY or LOCAL_MODEL_READY,
                "model_format":"ARIES deterministic task engine with optional local SmolLM2-360M-Instruct GGUF model and optional OpenAI-compatible backend",
                "trained_characters":MODEL.trained_characters,
                "next_step":"Local ARIES model is loaded." if LOCAL_MODEL_READY else ("Independent mode is active. Install a compatible local GGUF model to enable general chat; built-in deterministic tasks remain available." if INDEPENDENT_MODE else ("General chat backend is loaded." if UPSTREAM_READY else "Configure a local GGUF model or explicitly opt into an OpenAI-compatible upstream."))
            })
        if path == "/v1/models":
            return self.send_json(200, {"object":"list","data":[
                {"id":MODEL_ID,"object":"model","owned_by":"aries"}],
                "inference_ready":UPSTREAM_READY or LOCAL_MODEL_READY,
                "model_type":"OpenAI-compatible chat backend with ARIES native task engine" if UPSTREAM_READY else ("local SmolLM2-360M-Instruct" if LOCAL_MODEL_READY else "character n-gram baseline")})
        if path == "/performance":
            return self.send_json(200, {
                "service": "ARIES AI API",
                "fast_path_cache": FAST_PATH.snapshot(),
                "latency": LATENCY_MONITOR.snapshot(),
                "notice": "In-process measured elapsed times only; no sub-nanosecond guarantee."
            })
        if path == "/math/diagnostics":
            return self.send_json(200, {
                "module":"ARIES PRISE unified mathematics",
                "available_operators":["digital_root_369","toroidal_geometry","helixo_spiral",
                    "sample_signal_diagnostics","euler_characteristic","finite_euler_product",
                    "prise_scoring","small_instance_exact_sat"],
                "p_vs_np_status":"No proof of P=NP or P!=NP is claimed.",
                "latency_claim":"MEASURE_REQUIRED"
            })
        return self.send_json(404, {"error":{"message":"Not found","type":"not_found"}})
    def do_POST(self):
        path = urlparse(self.path).path
        if path not in {"/v1/chat/completions", "/reasoning/analyze", "/math/analyze", "/math/prise", "/math/sat"}:
            return self.send_json(404, {"error":{"message":"Not found","type":"not_found"}})
        try:
            size = int(self.headers.get("Content-Length","0"))
            if size <= 0 or size > 1_000_000:
                return self.send_json(400, {"error":{"message":"Request body must be 1 byte to 1 MB."}})
            body = json.loads(self.rfile.read(size))
            if path == "/reasoning/analyze":
                question = body.get("question", "")
                if not isinstance(question, str) or not question.strip():
                    return self.send_json(400, {"error":{"message":"question must be a non-empty string"}})
                return self.send_json(200, {
                    "module": "ARIES evidence-aware reasoning scaffold",
                    "result": analyze_request(question),
                    "notice": "Question decomposition is a planning aid, not proof of correctness or independent fact verification."
                })
            if path == "/math/analyze":
                payload = body.get("payload", "")
                if not isinstance(payload, str):
                    return self.send_json(400, {"error":{"message":"payload must be a string"}})
                result = MATH_ENGINE.analyze_binary_stream(payload.encode("utf-8"))
                return self.send_json(200, {"module":"ARIES PRISE unified mathematics", "result":result})
            if path == "/math/prise":
                problem = PRISEProblem(
                    name=str(body.get("name", "unnamed")),
                    priority=float(body["priority"]), risk=float(body["risk"]),
                    impact=float(body["impact"]), systemic=float(body["systemic"]),
                    emergent=float(body["emergent"]), notes=str(body.get("notes", "")))
                return self.send_json(200, {"module":"ARIES PRISE unified mathematics",
                                            "result":problem.to_dict()})
            if path == "/math/sat":
                clauses = body.get("clauses")
                variables = body.get("variable_count")
                if not isinstance(clauses, list) or not isinstance(variables, int) or isinstance(variables, bool):
                    return self.send_json(400, {"error":{"message":"clauses must be a list and variable_count an integer"}})
                result = exact_sat_bruteforce(clauses, variables)
                return self.send_json(200, {"module":"ARIES PRISE unified mathematics", "result":result,
                                            "notice":"Exhaustive SAT baseline; exponential-time and not a P-vs-NP proof."})
            messages = body.get("messages")
            if not isinstance(messages,list) or not messages or len(messages) > 256:
                return self.send_json(400, {"error":{"message":"messages must be a non-empty list with at most 256 items"}})
            normalized_messages = []
            for item in messages:
                if not isinstance(item,dict):
                    continue
                role = item.get("role")
                content = item.get("content")
                if role not in {"system","user","assistant"} or not isinstance(content,str):
                    continue
                if content.strip():
                    normalized_messages.append({"role":role,"content":content})
            if not any(item["role"] == "system" for item in normalized_messages):
                normalized_messages.insert(0, {"role": "system", "content": (
                    "You are ARIES AI, a capable general-purpose assistant. Answer the exact question, "
                    "reason carefully, show the key steps for complex tasks, check calculations, and "
                    "provide complete working solutions when asked to code. Use prior conversation context. "
                    "Separate verified facts from assumptions, never fabricate sources or claim actions you "
                    "did not perform, and state uncertainty when needed. Be direct and useful."
                )})
            user_messages = [item["content"] for item in normalized_messages if item["role"] == "user"]
            if not user_messages:
                return self.send_json(400, {"error":{"message":"At least one non-empty user message is required"}})
            prompt = user_messages[-1].strip()
            reasoning_plan = analyze_request(prompt)
            reasoning_context = build_reasoning_context(prompt)
            system_index = next((i for i, item in enumerate(normalized_messages) if item["role"] == "system"), None)
            if system_index is not None:
                normalized_messages[system_index]["content"] += "\n\n" + reasoning_context
            max_tokens = max(1,min(int(body.get("max_tokens",768)),2048))
            temperature = max(0.0,min(float(body.get("temperature",0.7)),2.0))
            started_ns = time.perf_counter_ns()
            answer = answer_known_question(prompt)
            math_route = None
            upstream_used = False
            upstream_elapsed_ns = None
            local_model_used = False
            local_model_elapsed_ns = None
            fast_path_cache_hit = False
            fast_path_elapsed_ns = 0
            if answer is None and LOCAL_MODEL_READY:
                answer, local_model_elapsed_ns = LOCAL_MODEL.generate(
                    normalized_messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                local_model_used = True
            if answer is None and UPSTREAM_READY:
                answer, upstream_elapsed_ns = request_upstream_answer(
                    normalized_messages,
                    base_url=UPSTREAM_BASE_URL,
                    model_id=UPSTREAM_MODEL_ID,
                    api_key=UPSTREAM_API_KEY,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout_seconds=UPSTREAM_TIMEOUT_SECONDS,
                )
                upstream_used = True
            if answer is None:
                answer, fast_path_cache_hit, fast_path_elapsed_ns = FAST_PATH.solve_with_metadata(prompt)
            if answer is None:
                math_result = route_math_prompt(prompt)
                if math_result is not None:
                    answer = math_result["answer"]
                    math_route = math_result["route"]
            if answer is None:
                answer = (
                    "I can handle supported calculations and built-in ARIES tasks, but the local "
                    "general-purpose model is not installed. Add a compatible GGUF model file and "
                    "set ARIES_GGUF_MODEL_PATH. Independent mode does not contact external AI providers."
                )
            elapsed_ns = max(1, time.perf_counter_ns() - started_ns)
            LATENCY_MONITOR.record("chat_completion", elapsed_ns)
            if not isinstance(answer,str) or not answer.strip():
                raise UpstreamInferenceError("The inference backend returned an empty answer.", 502)
            return self.send_json(200, {
                "id":"chatcmpl-aries-native","object":"chat.completion",
                "created":int(time.time()),"model":MODEL_ID,
                "choices":[{"index":0,"message":{"role":"assistant","content":answer},
                            "finish_reason":"stop"}],
                "usage":{"prompt_tokens":len(prompt),"completion_tokens":len(answer),
                         "total_tokens":len(prompt)+len(answer)},
                "aries_native":{
                    "runtime":"openai-compatible-upstream" if upstream_used else ("llama-cpp-local" if local_model_used else "stdlib-char-ngram+rules"),
                    "inference_seconds":round(elapsed_ns / 1000000000, 9),
                    "inference_ns":elapsed_ns,
                    "fast_path_elapsed_ns":fast_path_elapsed_ns,
                    "fast_path_cache_hit":fast_path_cache_hit,
                    "upstream_used":upstream_used,
                    "upstream_inference_ns":upstream_elapsed_ns,
                    "local_model_inference_ns":local_model_elapsed_ns,
                    "model_type":"configured_chat_model" if upstream_used else ("local_instruct_model" if local_model_used else "native_task_engine_or_baseline"),
                    "math_route":math_route,
                    "reasoning_scaffold_applied":True,
                    "reasoning_goal":reasoning_plan["goal"]
                }
            })
        except UpstreamInferenceError as exc:
            return self.send_json(exc.status_code, {"error":{"message":str(exc),"type":"inference_backend_error"}})
        except LocalInferenceError as exc:
            return self.send_json(502, {"error":{"message":str(exc),"type":"local_inference_error"}})
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
            return self.send_json(400, {"error":{"message":"Invalid request: "+str(exc)}})
    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

if __name__ == "__main__":
    print(f"ARIES native gateway listening on {HOST}:{PORT}; model={MODEL_ID}; chars={MODEL.trained_characters}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
