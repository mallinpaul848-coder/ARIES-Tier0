"""Local GGUF instruction-model adapter for ARIES."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path


class LocalInferenceError(RuntimeError):
    pass


class LocalChatModel:
    """Thread-safe CPU inference over an instruction-tuned GGUF model."""

    def __init__(self, model_path: str | None = None):
        path = Path(
            model_path
            or os.getenv(
                "ARIES_GGUF_MODEL_PATH",
                "/app/models/SmolLM2-360M-Instruct-Q3_K_M.gguf",
            )
        )
        if not path.is_file():
            raise FileNotFoundError(f"Local GGUF model file is missing: {path}")
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("llama-cpp-python is not installed.") from exc

        try:
            self._model = Llama(
                model_path=str(path),
                n_ctx=max(512, min(int(os.getenv("ARIES_LOCAL_CONTEXT_SIZE", "512")), 2048)),
                n_threads=max(1, min(int(os.getenv("ARIES_LOCAL_MODEL_THREADS", "1")), 4)),
                n_batch=16,
                n_gpu_layers=0,
                use_mmap=True,
                verbose=False,
            )
        except Exception as exc:
            raise RuntimeError(f"Could not load the local instruction model ({type(exc).__name__}).") from None
        self.model_path = str(path)
        self._lock = threading.Lock()

    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 128,
        temperature: float = 0.2,
    ) -> tuple[str, int]:
        normalized = []
        for item in messages:
            if not isinstance(item, dict):
                continue
            role, content = item.get("role"), item.get("content")
            if role in {"system", "user", "assistant"} and isinstance(content, str) and content.strip():
                normalized.append({"role": role, "content": content[-1200:]})
        if not any(item["role"] == "user" for item in normalized):
            raise LocalInferenceError("A non-empty user message is required.")
        system_message = next(
            (item for item in normalized if item["role"] == "system"),
            {
                "role": "system",
                "content": (
                    "You are ARIES AI, the assistant in the MALLIN platform. First identify what the user "
                    "is actually asking, then answer that question directly. Use the full "
                    "conversation context and do not repeat generic introductions. Follow "
                    "requested formats exactly. For calculations, show a short checkable "
                    "working when useful. Distinguish facts from estimates; never invent "
                    "sources, capabilities, actions, or current events. If a question needs "
                    "current information you do not have, say what is uncertain. Be useful, "
                    "specific, and concise unless the user asks for detail. "
                    "For complex work, apply PRISE: identify Priority, Risk, Impact, Systemic "
                    "effects, and Emergent behavior; state assumptions; split the task into "
                    "checkable steps; and verify calculations and consistency before answering. "
                    "Use Mallin 3-6-9 digital-root, mod-3/mod-9, vortex-cycle, Phase-8, and Helixo "
                    "features only when relevant as deterministic descriptors or candidate "
                    "heuristics, never as substitutes for a derivation or evidence. For SAT and "
                    "Millennium Prize research, state the exact claim, definitions, complexity "
                    "bound, proof obligations, and counterexample checks; distinguish verified "
                    "results from conjectures and experiments, and never claim a problem solved "
                    "without an independently checkable proof. For general questions, answer the "
                    "actual question instead of forcing mathematical symbolism into it."
                ),
            },
        )
        # Bound prompt prefill for the one-vCPU public instance; long chat histories
        # otherwise waste most of the small model's 512-token context.
        system_message = {"role": "system", "content": system_message["content"][:900]}
        recent_messages = [item for item in normalized if item["role"] != "system"][-4:]
        normalized = [system_message, *recent_messages]
        started_ns = time.perf_counter_ns()
        print(f"ARIES local inference started; messages={len(recent_messages)}; prompt_chars={sum(len(x["content"]) for x in normalized)}", flush=True)
        try:
            with self._lock:
                response = self._model.create_chat_completion(
                    messages=normalized,
                    max_tokens=max(1, min(int(max_tokens), 384)),
                    temperature=max(0.0, min(float(temperature), 1.2)),
                    top_p=0.9,
                    repeat_penalty=1.08,
                )
        except Exception as exc:
            raise LocalInferenceError(
                f"Local model inference failed ({type(exc).__name__})."
            ) from None

        choices = response.get("choices", []) if isinstance(response, dict) else []
        message = choices[0].get("message", {}) if choices else {}
        answer = message.get("content") if isinstance(message, dict) else None
        if not isinstance(answer, str) or not answer.strip():
            raise LocalInferenceError("Local model returned an empty answer.")
        elapsed_ns = max(1, time.perf_counter_ns() - started_ns)
        print(f"ARIES local inference completed; elapsed_ms={elapsed_ns / 1_000_000:.1f}; answer_chars={len(answer.strip())}", flush=True)
        return answer.strip(), elapsed_ns
