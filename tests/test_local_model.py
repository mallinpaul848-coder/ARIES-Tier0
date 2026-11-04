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
    assert len(forwarded) == 5
    assert [item["content"] for item in forwarded[1:]] == [
        "Question 8",
        "Question 9",
        "Question 10",
        "Question 11",
    ]


def test_local_chat_rejects_empty_model_output():
    model = build_model("   ")
    with pytest.raises(LocalInferenceError, match="empty answer"):
        model.generate([{"role": "user", "content": "Hello"}])


def test_local_chat_requires_user_message():
    model = build_model()
    with pytest.raises(LocalInferenceError, match="user message"):
        model.generate([{"role": "assistant", "content": "Previous answer"}])


def test_local_chat_metadata_separates_lock_wait_from_model_compute():
    model = build_model()
    answer, total_ns, lock_wait_ns, compute_ns = model.generate_with_metadata(
        [{"role": "user", "content": "What is 2 + 2?"}],
        max_tokens=12,
        temperature=0,
    )
    assert answer == "Paris"
    assert total_ns > 0
    assert lock_wait_ns >= 0
    assert compute_ns > 0
    assert total_ns >= lock_wait_ns
    assert total_ns >= compute_ns


def test_local_chat_metadata_measures_lock_contention():
    model = build_model()
    model._lock.acquire()
    results = []
    finished = threading.Event()

    def run():
        try:
            results.append(model.generate_with_metadata(
                [{"role": "user", "content": "Hello"}]
            ))
        finally:
            finished.set()

    worker = threading.Thread(target=run)
    worker.start()
    # Wait until the worker has started and is attempting generation.
    import time
    time.sleep(0.03)
    model._lock.release()
    worker.join(timeout=2)
    assert finished.is_set()
    assert results
    assert results[0][2] > 0
