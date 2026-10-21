import threading

import pytest

from software.local_model import LocalChatModel, LocalInferenceError


class FakeLlama:
    def __init__(self, answer="Paris"):
        self.answer = answer
        self.payload = None

    def create_chat_completion(self, **kwargs):
        self.payload = kwargs
        return {
            "choices": [
                {"message": {"role": "assistant", "content": self.answer}}
            ]
        }


def build_model(answer="Paris"):
    model = object.__new__(LocalChatModel)
    model._model = FakeLlama(answer)
    model._lock = threading.Lock()
    model.model_path = "test-model.gguf"
    return model


def test_local_chat_returns_assistant_answer_and_elapsed_time():
    model = build_model()
    answer, elapsed_ns = model.generate(
        [{"role": "user", "content": "What is the capital of France?"}],
        max_tokens=24,
        temperature=0,
    )
    assert answer == "Paris"
    assert elapsed_ns > 0
    assert model._model.payload["messages"][0]["role"] == "system"
    assert model._model.payload["messages"][-1] == {
        "role": "user",
        "content": "What is the capital of France?",
    }


def test_local_chat_keeps_system_prompt_and_only_recent_messages():
    model = build_model()
    history = [{"role": "system", "content": "Custom ARIES instructions"}]
    for number in range(12):
        history.append({"role": "user", "content": f"Question {number}"})
    model.generate(history)
    forwarded = model._model.payload["messages"]
    assert forwarded[0] == {"role": "system", "content": "Custom ARIES instructions"}
    assert len(forwarded) == 9
    assert forwarded[-1]["content"] == "Question 11"


def test_local_chat_rejects_empty_model_output():
    model = build_model("   ")
    with pytest.raises(LocalInferenceError, match="empty answer"):
        model.generate([{"role": "user", "content": "Hello"}])


def test_local_chat_requires_user_message():
    model = build_model()
    with pytest.raises(LocalInferenceError, match="user message"):
        model.generate([{"role": "assistant", "content": "Previous answer"}])
