#!/usr/bin/env python3
"""Shared eval config loader.

Loads analyzer and judge model settings from eval/configs/eval_models.yml,
expanding environment variables. Used by run_analyzer.py, run_judge.py,
and the optimizer's fitness.py.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import yaml


def _expand_env_vars(value: str) -> str:
    """Expand ${VAR} and $VAR references in a string."""
    return re.sub(
        r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)',
        lambda m: os.environ.get(m.group(1) or m.group(2), m.group(0)),
        value,
    )


def _expand_dict(d: dict) -> dict:
    """Recursively expand env vars in all string values."""
    result = {}
    for k, v in d.items():
        if isinstance(v, str):
            result[k] = _expand_env_vars(v)
        elif isinstance(v, dict):
            result[k] = _expand_dict(v)
        else:
            result[k] = v
    return result


def load_eval_config(config_path: Optional[str] = None) -> dict:
    """Load eval_models.yml and return expanded config dict.

    Args:
        config_path: Path to eval_models.yml. If None, auto-discovers
                     relative to this file's location.

    Returns:
        Dict with 'analyzer' and 'judge' keys, each containing
        base_url, api_key, model, max_tokens, temperature.
    """
    if config_path is None:
        config_path = str(Path(__file__).parent / "configs" / "eval_models.yml")

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Eval config not found: {path}")

    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return _expand_dict(raw)


def get_analyzer_config(config_path: Optional[str] = None) -> dict:
    """Get just the analyzer model config."""
    return load_eval_config(config_path).get("analyzer", {})


def get_judge_config(config_path: Optional[str] = None) -> dict:
    """Get just the judge model config."""
    return load_eval_config(config_path).get("judge", {})
