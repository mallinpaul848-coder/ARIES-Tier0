"""Bounded model/tool/final-answer loop for ARIES.

Only the server-defined aries_calculate tool is exposed. It dispatches to the
existing allow-listed deterministic operation handler; no arbitrary code runs.
"""
from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

MAX_TOOL_ROUNDS = 3

TOOL_DEFINITIONS = [{
    "type": "function",
    "function": {
        "name": "aries_calculate",
        "description": (
            "Use exact ARIES math when needed. Supported operations: digital_root, gcd, "
            "lcm, is_prime, dot_product, matrix_multiply, integer_mix."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": [
                    "digital_root", "gcd", "lcm", "is_prime",
                    "dot_product", "matrix_multiply", "integer_mix"
                ]},
                "parameters": {"type": "object"}
            },
            "required": ["operation", "parameters"],
            "additionalProperties": False
        }
    }
}]


async def run_tool_loop(
    payload: dict[str, Any],
    post_json: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    execute_operation: Callable[[str, dict[str, Any]], Any],
    *,
    max_rounds: int = MAX_TOOL_ROUNDS,
) -> dict[str, Any]:
    """Return the model's final completion after up to max_rounds tool rounds."""
    if not 1 <= max_rounds <= 6:
        raise ValueError("max_rounds must be between 1 and 6")
    working = dict(payload)
    working["messages"] = [dict(m) for m in payload.get("messages", [])]
    # Never accept client-supplied tools; tool permissions are server-controlled.
    working["tools"] = TOOL_DEFINITIONS
    working["tool_choice"] = "auto"

    for _ in range(max_rounds + 1):
        response = await post_json(working)
        choices = response.get("choices") or []
        if not choices or not isinstance(choices[0], dict):
            return response
        message = choices[0].get("message") or {}
        calls = message.get("tool_calls") or []
        if not calls:
            return response

        working["messages"].append({
            "role": "assistant",
            "content": message.get("content"),
            "tool_calls": calls,
        })
        for call in calls:
            call_id = call.get("id") or "aries-invalid-tool-call"
            function = call.get("function") or {}
            name = function.get("name", "")
            raw_args = function.get("arguments", "{}")
            try:
                if name != "aries_calculate":
                    raise ValueError("tool is not allow-listed")
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                if not isinstance(args, dict):
                    raise ValueError("tool arguments must be a JSON object")
                operation = args.get("operation")
                parameters = args.get("parameters", {})
                if not isinstance(operation, str) or not isinstance(parameters, dict):
                    raise ValueError("operation and parameters are required")
                result = execute_operation(operation, parameters)
                content = json.dumps({"ok": True, "result": result}, separators=(",", ":"))
            except Exception as exc:
                content = json.dumps({"ok": False, "error": str(exc)[:300]}, separators=(",", ":"))
            working["messages"].append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": name or "aries_calculate",
                "content": content,
            })

    return {
        "id": "chatcmpl-aries-tool-limit",
        "object": "chat.completion",
        "model": payload.get("model", "unknown"),
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "I couldn't finish within the calculation tool limit. Please simplify the request."
            },
            "finish_reason": "stop"
        }],
        "aries_runtime": {"tool_loop_limited": True, "max_tool_rounds": max_rounds}
    }
