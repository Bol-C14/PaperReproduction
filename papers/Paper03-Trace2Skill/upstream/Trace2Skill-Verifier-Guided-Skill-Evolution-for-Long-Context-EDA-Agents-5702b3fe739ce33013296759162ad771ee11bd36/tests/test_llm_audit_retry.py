from __future__ import annotations

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from llm_audit import chat_completion  # noqa: E402


class _TransientGatewayError(Exception):
    status_code = 504


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            raise _TransientGatewayError("504 Gateway Time-out")
        return {"ok": True, "kwargs": kwargs}


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()


def test_chat_completion_retries_transient_gateway_error(monkeypatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("llm_audit.time.sleep", lambda secs: sleeps.append(secs))
    monkeypatch.setattr("llm_audit.random.uniform", lambda _a, _b: 0.0)
    client = _FakeClient()

    response = chat_completion(
        client,
        "fake-model",
        [{"role": "user", "content": "hello"}],
        retry_attempts=2,
        retry_base_sleep=0.01,
    )

    assert response["ok"] is True
    assert client.chat.completions.calls == 2
    assert sleeps == [0.01]
