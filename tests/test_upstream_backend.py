import json

import pytest

from software.upstream_backend import (
    UpstreamInferenceError,
    chat_completions_url,
    request_upstream_answer,
)


def test_chat_url_normalizes_common_provider_urls():
    assert chat_completions_url("https://api.example.com") == (
        "https://api.example.com/v1/chat/completions"
    )
    assert chat_completions_url("https://api.example.com/v1/") == (
        "https://api.example.com/v1/chat/completions"
    )
    assert chat_completions_url("https://api.example.com/v1/chat/completions") == (
        "https://api.example.com/v1/chat/completions"
    )


def test_invalid_upstream_url_is_rejected():
    with pytest.raises(ValueError, match="valid HTTP"):
        chat_completions_url("not-a-url")


def test_request_forwards_model_and_conversation_with_auth(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self, _limit):
            return json.dumps({
                "choices": [{
                    "message": {"role": "assistant", "content": "The answer is 42."}
                }]
            }).encode()

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["payload"] = json.loads(req.data.decode())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("software.upstream_backend.request.urlopen", fake_urlopen)
    answer, elapsed_ns = request_upstream_answer(
        [
            {"role": "user", "content": "What is the answer?"},
            {"role": "assistant", "content": "Let me think."},
            {"role": "user", "content": "What is 6 times 7?"},
        ],
        base_url="https://provider.example/v1",
        model_id="mallin-chat-test",
        api_key="secret-test-key",
        max_tokens=80,
        temperature=0.1,
        timeout_seconds=12,
    )

    assert answer == "The answer is 42."
    assert elapsed_ns > 0
    assert captured["url"] == "https://provider.example/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer secret-test-key"
    assert captured["payload"]["model"] == "mallin-chat-test"
    assert captured["payload"]["messages"][-1] == {
        "role": "user",
        "content": "What is 6 times 7?",
    }
    assert captured["payload"]["messages"][0]["role"] == "system"
    assert captured["timeout"] == 12


def test_empty_provider_answer_fails_instead_of_fabricating_text(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self, _limit):
            return b'{"choices":[{"message":{"content":"  "}}]}'

    monkeypatch.setattr(
        "software.upstream_backend.request.urlopen",
        lambda *_args, **_kwargs: FakeResponse(),
    )
    with pytest.raises(UpstreamInferenceError, match="empty answer"):
        request_upstream_answer(
            [{"role": "user", "content": "Tell me something."}],
            base_url="https://provider.example/v1",
            model_id="example-model",
        )


def test_unconfigured_general_chat_returns_service_unavailable():
    with pytest.raises(UpstreamInferenceError) as exc:
        request_upstream_answer(
            [{"role": "user", "content": "What is the capital of France?"}],
            base_url="",
            model_id="",
        )
    assert exc.value.status_code == 503
