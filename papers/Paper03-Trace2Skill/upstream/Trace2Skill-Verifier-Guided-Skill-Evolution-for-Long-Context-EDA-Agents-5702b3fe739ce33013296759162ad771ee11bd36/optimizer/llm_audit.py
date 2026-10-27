#!/usr/bin/env python3
"""LLM Audit Log — records every optimizer-side LLM call for post-hoc analysis.

Captures:
  - Full prompt text (system + user + any substitutions)
  - Full response text
  - Token usage (prompt / completion / reasoning)
  - Latency, finish_reason, errors
  - Explicit context: generation, purpose, task, individual (wherever applicable)

Layout under a run's output directory:

    <run_dir>/
    ├── llm_calls.jsonl              ← index: one JSON object per call
    └── gen<N>/prompts/
        ├── <call_id>_prompt.txt     ← full prompt text
        └── <call_id>_response.txt   ← raw response text

The JSONL index lets you quickly filter (e.g., by purpose, generation, latency)
without loading thousands of text files. The prompt/response files give you
the full content for any call you want to inspect.

Usage — the simplest path:

    logger = LLMAuditLogger(run_dir=Path("outputs/haiku_run"))
    logger.set_generation(1)
    response = chat_completion(
        client, model, messages,
        audit_logger=logger,
        purpose="layer1_refine",
        context={"task": "reckon_0001", "outcome": "fail", "rollout_id": "ind0_r3"},
        temperature=0.0,
        max_tokens=16384,
    )

If `audit_logger` is None, falls through to a plain `client.chat.completions.create`.
"""

from __future__ import annotations

import json
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import openai


def _is_retryable_llm_error(exc: Exception) -> bool:
    """Return whether an optimizer-side LLM call should be retried.

    The optimizer's mutator/oracle calls are long-context requests routed
    through remote endpoints. Transient 5xx/504 gateway failures should not
    silently collapse an evolutionary step into "keep parent"; semantic gates
    should decide skill quality, not one flaky HTTP response.
    """
    retryable_types = tuple(
        cls
        for name in (
            "APITimeoutError",
            "APIConnectionError",
            "RateLimitError",
            "InternalServerError",
        )
        if isinstance((cls := getattr(openai, name, None)), type)
    )
    if retryable_types and isinstance(exc, retryable_types):
        return True
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int) and status_code in {408, 409, 429, 500, 502, 503, 504}:
        return True
    text = str(exc).lower()
    return any(marker in text for marker in ("504 gateway", "502 bad gateway", "503 service", "timeout"))


@dataclass
class LLMAuditLogger:
    """Writes a per-call audit trail of every LLM invocation during a run.

    Two modes controlled by `write_prompt_files`:
      - True  (debug mode): writes full prompt + response .txt files per call
      - False (prod  mode): only appends to llm_calls.jsonl index (tokens,
        latency, purpose, context) — saves disk for long runs where you don't
        need to inspect individual prompts.
    """

    run_dir: Path
    enabled: bool = True
    write_prompt_files: bool = True
    _current_generation: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.run_dir = Path(self.run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.run_dir / "llm_calls.jsonl"

    def set_generation(self, gen: int) -> None:
        """Switch the logger's active generation bucket (controls which
        `gen<N>/prompts/` directory new prompt files land in)."""
        self._current_generation = gen

    def _prompts_dir(self) -> Path:
        d = self.run_dir / f"gen{self._current_generation}" / "prompts"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def log_call(
        self,
        client: openai.OpenAI,
        model: str,
        messages: list[dict[str, Any]],
        purpose: str,
        context: Optional[dict[str, Any]] = None,
        **create_kwargs: Any,
    ) -> Any:
        """Make a chat-completion API call and record it in the audit log.

        Returns the raw OpenAI response object (same as `client.chat.completions.create`).
        Re-raises any exception after logging the failure.
        """
        call_id = uuid.uuid4().hex[:12]
        start_ts = time.time()

        # Render prompt text (all messages concatenated with role headers)
        prompt_text = "\n\n".join(
            f"=== [{m.get('role', '?')}] ===\n{m.get('content', '')}"
            for m in messages
        )

        prompts_dir = self._prompts_dir() if self.write_prompt_files else None
        prompt_path: Optional[Path] = None
        if self.write_prompt_files and prompts_dir is not None:
            prompt_path = prompts_dir / f"{call_id}_prompt.txt"
            prompt_path.write_text(prompt_text, encoding="utf-8")

        response: Any = None
        response_text = ""
        finish_reason: Optional[str] = None
        prompt_tokens = 0
        completion_tokens = 0
        reasoning_tokens = 0
        error_str: Optional[str] = None

        try:
            response = client.chat.completions.create(
                model=model, messages=messages, **create_kwargs
            )
            choice = response.choices[0]
            response_text = choice.message.content or ""
            finish_reason = choice.finish_reason
            usage = getattr(response, "usage", None)
            if usage is not None:
                prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(usage, "completion_tokens", 0) or 0
                details = getattr(usage, "completion_tokens_details", None)
                if details is not None:
                    reasoning_tokens = getattr(details, "reasoning_tokens", 0) or 0
            return response
        except Exception as e:
            error_str = f"{type(e).__name__}: {e}"
            raise
        finally:
            elapsed = time.time() - start_ts

            # Save response text if in debug mode
            response_path: Optional[Path] = None
            if self.write_prompt_files and prompts_dir is not None:
                response_path = prompts_dir / f"{call_id}_response.txt"
                response_path.write_text(response_text or f"(empty; error={error_str})", encoding="utf-8")

            # Append JSONL entry
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "call_id": call_id,
                "generation": self._current_generation,
                "purpose": purpose,
                "context": context or {},
                "model": model,
                "prompt_chars": len(prompt_text),
                "response_chars": len(response_text),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "reasoning_tokens": reasoning_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "elapsed_secs": round(elapsed, 3),
                "finish_reason": finish_reason,
                "error": error_str,
                "prompt_file": str(prompt_path.relative_to(self.run_dir)) if prompt_path else None,
                "response_file": str(response_path.relative_to(self.run_dir)) if response_path else None,
            }

            if self.enabled:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def chat_completion(
    client: openai.OpenAI,
    model: str,
    messages: list[dict[str, Any]],
    audit_logger: Optional[LLMAuditLogger] = None,
    purpose: str = "unknown",
    context: Optional[dict[str, Any]] = None,
    **create_kwargs: Any,
) -> Any:
    """Chat-completion wrapper that optionally records the call to an audit log.

    If `audit_logger` is None, falls through to a plain
    `client.chat.completions.create(...)` call — no side effects, no overhead.

    If `audit_logger` is provided, the call is logged (prompt, response, tokens,
    latency, purpose, context) and the raw response is still returned.
    """
    retry_attempts = int(create_kwargs.pop("retry_attempts", 3))
    retry_base_sleep = float(create_kwargs.pop("retry_base_sleep", 10.0))
    retry_attempts = max(1, retry_attempts)

    for attempt in range(1, retry_attempts + 1):
        try:
            if audit_logger is None:
                return client.chat.completions.create(model=model, messages=messages, **create_kwargs)

            return audit_logger.log_call(
                client=client,
                model=model,
                messages=messages,
                purpose=purpose,
                context={**(context or {}), "attempt": attempt, "max_attempts": retry_attempts},
                **create_kwargs,
            )
        except Exception as exc:
            if attempt >= retry_attempts or not _is_retryable_llm_error(exc):
                raise
            sleep_time = min(120.0, retry_base_sleep * (2 ** (attempt - 1))) + random.uniform(0.0, 2.0)
            print(
                f"  [llm-retry] {purpose} attempt {attempt}/{retry_attempts} failed with "
                f"{type(exc).__name__}; retrying in {sleep_time:.1f}s"
            )
            time.sleep(sleep_time)

    raise RuntimeError("unreachable chat_completion retry state")


# ── Reproducibility metadata helpers ─────────────────────────────


def collect_run_metadata(repo_root: Path, skills_dir: Path) -> dict[str, Any]:
    """Capture reproducibility metadata at run start: git commit, library
    versions, OS info, and SHA-256 hashes of every skill file used by the
    optimizer. Lets you verify two runs used identical prompts."""
    import hashlib
    import platform
    import subprocess
    import sys

    metadata: dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "hostname": platform.node(),
    }

    # Git commit
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            metadata["git_commit"] = result.stdout.strip()
        result_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root, capture_output=True, text=True, timeout=5,
        )
        if result_status.returncode == 0:
            metadata["git_dirty"] = bool(result_status.stdout.strip())
    except Exception:
        metadata["git_commit"] = None

    # Key library versions
    versions: dict[str, str] = {}
    for pkg in ("openai", "pydantic", "ray", "yaml"):
        try:
            mod = __import__(pkg)
            versions[pkg] = getattr(mod, "__version__", "?")
        except Exception:
            pass
    metadata["library_versions"] = versions

    # Skill file hashes — any skill the optimizer loaded
    skills_dir = Path(skills_dir)
    skill_hashes: dict[str, str] = {}
    if skills_dir.exists():
        for md_file in sorted(skills_dir.rglob("*.md")):
            content = md_file.read_bytes()
            rel = str(md_file.relative_to(skills_dir))
            skill_hashes[rel] = hashlib.sha256(content).hexdigest()
    metadata["skill_hashes"] = skill_hashes

    return metadata
