"""Offline unit tests for the optional GPT toolkit (no API key/network required)."""
import json
import sys
import types
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from software.gpt_toolkit import GPTToolkit


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=Mock(side_effect=self._create)))
        self.closed = False

    def _create(self, **kwargs):
        return next(self.responses)

    def close(self):
        self.closed = True


def response(content="ok", tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.fixture
def toolkit(monkeypatch):
    fake_sdk = types.ModuleType("openai")
    fake_sdk.OpenAI = Mock()
    monkeypatch.setitem(sys.modules, "openai", fake_sdk)
    instance = GPTToolkit(api_key="test-key")
    instance.client = FakeClient([response("hello"), response("second")])
    return instance


def test_chat_records_successful_turn_only(toolkit):
    assert toolkit.chat(" hi ") == "hello"
    assert toolkit._history[-2:] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_empty_prompt_rejected_before_api_call(toolkit):
    with pytest.raises(ValueError, match="non-empty"):
        toolkit.chat("   ")
    assert toolkit.client.chat.completions.create.call_count == 0


def test_reset_conversation_preserves_new_system_prompt(toolkit):
    toolkit.chat("hello")
    toolkit.reset_conversation("Be concise.")
    assert toolkit._history == [{"role": "system", "content": "Be concise."}]


def test_history_is_bounded(toolkit):
    toolkit.max_history_messages = 4
    for i in range(5):
        toolkit._history.extend([
            {"role": "user", "content": f"q{i}"},
            {"role": "assistant", "content": f"a{i}"},
        ])
    trimmed = toolkit._trim(toolkit._history)
    assert trimmed[0]["role"] == "system"
    assert len(trimmed) == 4
    assert trimmed[-1]["content"] == "a4"


def test_structured_json_uses_json_mode(monkeypatch, toolkit):
    toolkit.client = FakeClient([response('{"ok": true, "count": 3}')])
    result = toolkit.get_structured_json("Return status", json_schema_name="status")
    assert result == {"ok": True, "count": 3}
    kwargs = toolkit.client.chat.completions.create.call_args.kwargs
    assert kwargs["response_format"] == {"type": "json_object"}


def test_structured_json_supports_strict_schema(toolkit):
    toolkit.client = FakeClient([response('{"ok": true}')])
    schema = {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
        "required": ["ok"],
        "additionalProperties": False,
    }
    assert toolkit.get_structured_json("Return status", schema=schema) == {"ok": True}
    fmt = toolkit.client.chat.completions.create.call_args.kwargs["response_format"]
    assert fmt["json_schema"]["strict"] is True


def test_invalid_json_is_reported(toolkit):
    toolkit.client = FakeClient([response("not json")])
    with pytest.raises(RuntimeError, match="valid JSON"):
        toolkit.get_structured_json("Return JSON")


def test_tool_calls_are_allowlisted_and_executed(toolkit):
    call = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="multiply", arguments='{"a": 6, "b": 7}'),
    )
    tool_message = SimpleNamespace(
        content=None,
        tool_calls=[call],
        model_dump=lambda exclude_none=True: {
            "role": "assistant",
            "tool_calls": [{
                "id": "call-1",
                "type": "function",
                "function": {"name": "multiply", "arguments": '{"a": 6, "b": 7}'},
            }],
        },
    )
    toolkit.client = FakeClient([
        SimpleNamespace(choices=[SimpleNamespace(message=tool_message)]),
        response("42"),
    ])
    tools = [{
        "type": "function",
        "function": {"name": "multiply", "parameters": {"type": "object"}},
    }]
    assert toolkit.execute_with_tools(
        "multiply 6 by 7", tools, {"multiply": lambda a, b: a * b}
    ) == "42"
    assert json.loads(toolkit.client.chat.completions.create.call_args_list[0].kwargs["messages"][-1]["content"]) == 42


def test_unmatched_tools_are_rejected(toolkit):
    with pytest.raises(ValueError, match="allowlisted"):
        toolkit.execute_with_tools(
            "do it",
            [{"type": "function", "function": {"name": "danger"}}],
            {},
        )


def test_client_can_be_closed(toolkit):
    toolkit.close()
    assert toolkit.client.closed
