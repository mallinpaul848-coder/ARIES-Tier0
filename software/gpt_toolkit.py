"""Optional OpenAI-compatible toolkit for ARIES.

This is an optional adapter; it does not replace or modify ARIES native inference.
Install the SDK with: pip install openai
Set OPENAI_API_KEY in the environment. Never hard-code API keys.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Iterator, Mapping, Sequence


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant. Be accurate, distinguish verified facts from "
    "uncertainty, and do not claim to have run tests or training unless it happened."
)


class GPTToolkit:
    """Small, testable chat adapter with bounded history and allowlisted tools."""

    def __init__(
        self,
        default_model: str = "gpt-4o-mini",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        api_key: str | None = None,
        max_history_messages: int = 40,
        max_tool_rounds: int = 4,
        timeout: float = 30.0,
    ) -> None:
        if not default_model.strip():
            raise ValueError("default_model must not be empty")
        if max_history_messages < 2:
            raise ValueError("max_history_messages must be at least 2")
        if max_tool_rounds < 1:
            raise ValueError("max_tool_rounds must be at least 1")
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Set it in your environment; do not commit it."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "The OpenAI SDK is required for this optional adapter. Run: pip install openai"
            ) from exc

        self.client = OpenAI(api_key=key, timeout=timeout)
        self.default_model = default_model
        self.system_prompt = system_prompt
        self.max_history_messages = max_history_messages
        self.max_tool_rounds = max_tool_rounds
        self._history: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

    @staticmethod
    def _check_prompt(prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        return prompt.strip()

    def _trim(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Keep the system message and newest messages; called between turns."""
        system = messages[0]
        recent = messages[1:][-(self.max_history_messages - 1):]
        return [system, *recent]

    def reset_conversation(self, system_prompt: str | None = None) -> None:
        """Clear prior turns, optionally replacing the system prompt."""
        if system_prompt is not None:
            self.system_prompt = system_prompt
        self._history = [{"role": "system", "content": self.system_prompt}]

    def chat(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> str:
        prompt = self._check_prompt(prompt)
        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        candidate = self._trim([*self._history, {"role": "user", "content": prompt}])
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=candidate,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        if not isinstance(content, str):
            raise RuntimeError("Model returned no text content")
        self._history = self._trim([*candidate, {"role": "assistant", "content": content}])
        return content

    def stream_chat(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> Iterator[str]:
        """Yield text chunks; commit the turn to history only after a clean stream."""
        prompt = self._check_prompt(prompt)
        candidate = self._trim([*self._history, {"role": "user", "content": prompt}])
        stream = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=candidate,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        parts: list[str] = []
        for event in stream:
            choices = getattr(event, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            piece = getattr(delta, "content", None) if delta is not None else None
            if piece:
                parts.append(piece)
                yield piece
        answer = "".join(parts)
        if not answer:
            raise RuntimeError("Model returned an empty stream")
        self._history = self._trim([*candidate, {"role": "assistant", "content": answer}])

    def get_structured_json(
        self,
        prompt: str,
        json_schema_name: str = "response",
        schema: Mapping[str, Any] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Return parsed JSON; use strict JSON Schema when a schema is supplied."""
        prompt = self._check_prompt(prompt)
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", json_schema_name):
            raise ValueError("json_schema_name must be 1-64 letters, digits, '_' or '-'")
        response_format: dict[str, Any]
        if schema is None:
            response_format = {"type": "json_object"}
            json_prompt = prompt + "\nReturn only a valid JSON object."
        else:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": json_schema_name,
                    "strict": True,
                    "schema": dict(schema),
                },
            }
            json_prompt = prompt
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": json_prompt},
            ],
            response_format=response_format,
            temperature=0,
        )
        content = response.choices[0].message.content
        try:
            parsed = json.loads(content or "")
        except (json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError("Model did not return valid JSON") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("Expected a JSON object, not an array or scalar")
        return parsed

    def execute_with_tools(
        self,
        prompt: str,
        tools: Sequence[dict[str, Any]],
        available_functions: Mapping[str, Callable[..., Any]],
        model: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        """Run only declared function tools that are explicitly allowlisted locally."""
        prompt = self._check_prompt(prompt)
        allowed: list[dict[str, Any]] = []
        allowed_names: set[str] = set()
        for tool in tools:
            if tool.get("type") != "function":
                continue
            function = tool.get("function", {})
            name = function.get("name")
            if isinstance(name, str) and name in available_functions and callable(available_functions[name]):
                allowed.append(tool)
                allowed_names.add(name)
        if not allowed:
            raise ValueError("No tools matched the locally allowlisted functions")

        messages = self._trim([*self._history, {"role": "user", "content": prompt}])
        for _ in range(self.max_tool_rounds):
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                tools=allowed,
                tool_choice="auto",
                temperature=temperature,
            )
            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None)
            if not tool_calls:
                answer = message.content
                if not isinstance(answer, str):
                    raise RuntimeError("Model returned no final text answer")
                self._history = self._trim([*messages, {"role": "assistant", "content": answer}])
                return answer

            dump = getattr(message, "model_dump", None)
            messages.append(dump(exclude_none=True) if callable(dump) else {
                "role": "assistant",
                "content": getattr(message, "content", None),
                "tool_calls": tool_calls,
            })
            for call in tool_calls:
                name = call.function.name
                if name not in allowed_names:
                    raise RuntimeError(f"Model requested a non-allowlisted tool: {name}")
                try:
                    arguments = json.loads(call.function.arguments or "{}")
                    if not isinstance(arguments, dict):
                        raise ValueError("Tool arguments must be a JSON object")
                    result = available_functions[name](**arguments)
                    result_text = json.dumps(result, ensure_ascii=False, default=str)
                except Exception as exc:
                    result_text = json.dumps({
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }, ensure_ascii=False)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result_text,
                })
        raise RuntimeError(f"Tool-call limit reached ({self.max_tool_rounds} rounds)")

    def close(self) -> None:
        """Close the underlying SDK client when the caller is finished."""
        self.client.close()


if __name__ == "__main__":
    toolkit = GPTToolkit()
    try:
        print(toolkit.chat("Reply with exactly: ARIES toolkit online"))
    finally:
        toolkit.close()
