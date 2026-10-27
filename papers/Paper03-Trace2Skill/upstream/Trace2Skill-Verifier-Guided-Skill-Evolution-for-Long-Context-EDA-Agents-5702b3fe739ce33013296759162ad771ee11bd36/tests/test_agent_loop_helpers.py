from __future__ import annotations

import sys
from http.cookies import SimpleCookie
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "nemogym"))

from responses_api_agents.cvdp_agentic_heavy_agent.app import (  # noqa: E402
    _function_call_names,
    _merge_cookies,
)


def test_function_call_names_handles_sanitized_dicts_and_objects() -> None:
    items = [
        {"type": "function_call", "name": "echo"},
        SimpleNamespace(type="function_call", name="iverilog"),
        {"type": "message", "role": "assistant"},
    ]

    assert _function_call_names(items) == ["echo", "iverilog"]


def test_merge_cookies_keeps_plain_string_values() -> None:
    cookies = SimpleCookie()
    cookies["session"] = "abc123"
    target: dict[str, str] = {}

    _merge_cookies(target, cookies)

    assert target == {"session": "abc123"}
    assert isinstance(target["session"], str)
