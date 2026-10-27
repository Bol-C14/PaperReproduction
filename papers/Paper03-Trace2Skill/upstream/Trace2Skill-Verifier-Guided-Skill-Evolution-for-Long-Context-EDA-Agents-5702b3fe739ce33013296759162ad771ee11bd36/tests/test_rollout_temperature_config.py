from __future__ import annotations

import sys
import json
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from fitness import (  # noqa: E402
    RolloutModelMismatchError,
    RolloutResponseError,
    run_rollouts,
    validate_rollout_model_consistency,
)


class _Completed:
    returncode = 0
    stdout = ""
    stderr = ""


def test_run_rollouts_uses_configured_temperature(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return _Completed()

    monkeypatch.setattr("subprocess.run", fake_run)

    run_rollouts(
        "ng_collect",
        tmp_path / "tasks.jsonl",
        tmp_path / "rollouts.jsonl",
        rollout_model_cfg={
            "base_url": "http://example.test/v1",
            "api_key": "test",
            "model": "test-model",
            "temperature": 0.35,
            "max_output_tokens": 1234,
        },
    )

    params = next(
        arg for arg in captured["cmd"]
        if str(arg).startswith("+responses_create_params=")
    )
    assert "temperature: 0.35" in params
    assert "max_output_tokens: 1234" in params


def test_run_rollouts_defaults_to_moderate_temperature(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return _Completed()

    monkeypatch.setattr("subprocess.run", fake_run)

    run_rollouts(
        "ng_collect",
        tmp_path / "tasks.jsonl",
        tmp_path / "rollouts.jsonl",
        rollout_model_cfg={"model": "test-model"},
    )

    params = next(
        arg for arg in captured["cmd"]
        if str(arg).startswith("+responses_create_params=")
    )
    assert "temperature: 0.4" in params


def test_rollout_model_consistency_accepts_expected_model(tmp_path) -> None:
    rollout_path = tmp_path / "rollouts.jsonl"
    rollout_path.write_text(
        json.dumps({"response": {"model": "expected-model"}}) + "\n"
        + json.dumps({"response": {"model": "expected-model"}}) + "\n",
        encoding="utf-8",
    )

    report = validate_rollout_model_consistency(
        rollout_path,
        "expected-model",
        report_path=tmp_path / "rollout_model_check.json",
    )

    assert report["ok"] is True
    assert report["observed_models"] == {"expected-model": 2}
    assert json.loads((tmp_path / "rollout_model_check.json").read_text())["status"] == "ok"


def test_rollout_model_consistency_rejects_stale_policy_server(tmp_path) -> None:
    rollout_path = tmp_path / "rollouts.jsonl"
    rollout_path.write_text(
        json.dumps({"response": {"model": "azure/anthropic/claude-haiku-4-5"}}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RolloutModelMismatchError, match="configured .*claude-opus-4-6"):
        validate_rollout_model_consistency(
            rollout_path,
            "azure/anthropic/claude-opus-4-6",
            report_path=tmp_path / "rollout_model_check.json",
        )

    report = json.loads((tmp_path / "rollout_model_check.json").read_text())
    assert report["status"] == "mismatch"
    assert report["observed_models"] == {"azure/anthropic/claude-haiku-4-5": 1}


def test_rollout_model_consistency_classifies_error_responses(tmp_path) -> None:
    rollout_path = tmp_path / "rollouts.jsonl"
    rollout_path.write_text(
        json.dumps({"response": {"model": "expected-model"}}) + "\n"
        + json.dumps({"response": {"model": "error", "id": "error-seed-session"}}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RolloutResponseError, match="invalid response artifacts"):
        validate_rollout_model_consistency(
            rollout_path,
            "expected-model",
            report_path=tmp_path / "rollout_model_check.json",
        )

    report = json.loads((tmp_path / "rollout_model_check.json").read_text())
    assert report["status"] == "response_error"
    assert report["observed_models"] == {"error": 1, "expected-model": 1}
    assert report["error_rollouts"] == 1
