#!/usr/bin/env python3
"""Debug-mode helpers: structured error log + per-phase timing tracker.

Purpose: capture signals that currently only print to stdout and would
otherwise disappear after a run. These are the #1 post-hoc debug signals
— "why did gen-2 drop?" usually traces to a non-fatal exception nobody
saw in the console scroll-back.

Usage:

    err_logger = ErrorLogger(run_dir=Path("outputs/haiku_run"))
    try:
        response = client.chat.completions.create(...)
    except Exception as e:
        err_logger.record(
            phase="oracle_layer1",
            generation=gen,
            context={"task": task_id, "rollout_id": rid},
            exception=e,
        )
        # ... fallback ...

    timer = GenTimer(gen_dir)
    with timer.phase("rollouts"):
        ... fitness evaluation ...
    with timer.phase("oracle"):
        ... 3-layer pipeline ...
    timer.write()  # → gen_dir/timing.json

Both writers are best-effort (never raise from their own I/O errors).
"""

from __future__ import annotations

import json
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class ErrorLogger:
    """Appends structured non-fatal error records to <run_dir>/errors.jsonl.

    Fatal exceptions (ones that abort the run) are already captured by the
    outer print/raise. This logger is specifically for swallowed exceptions
    that would otherwise only show up in stdout scroll-back — e.g., a Layer 1
    refinement failing for one rollout while other rollouts continue.
    """

    run_dir: Path
    enabled: bool = True

    def __post_init__(self) -> None:
        self.run_dir = Path(self.run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.run_dir / "errors.jsonl"

    def record(
        self,
        phase: str,
        exception: BaseException,
        generation: Optional[int] = None,
        context: Optional[dict[str, Any]] = None,
        severity: str = "warning",
    ) -> None:
        """Record a non-fatal exception. Never raises."""
        if not self.enabled:
            return
        try:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "severity": severity,
                "phase": phase,
                "generation": generation,
                "exception_type": type(exception).__name__,
                "exception_msg": str(exception),
                "context": context or {},
                "traceback": traceback.format_exception(type(exception), exception,
                                                        exception.__traceback__)[-6:],
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            # Never let the error logger itself kill the run
            pass

    def record_info(
        self,
        phase: str,
        message: str,
        generation: Optional[int] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record a non-exception diagnostic event (e.g., rate-limit throttle)."""
        if not self.enabled:
            return
        try:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "severity": "info",
                "phase": phase,
                "generation": generation,
                "message": message,
                "context": context or {},
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass


@dataclass
class GenTimer:
    """Per-generation phase timer. Writes gen_dir/timing.json at the end.

    Phases are arbitrary labels; duplicate labels accumulate (so you can
    measure total time across multiple sub-invocations).
    """

    gen_dir: Path
    enabled: bool = True
    start_ts: float = field(default_factory=time.time)
    phases: dict[str, float] = field(default_factory=dict)
    phase_counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.gen_dir = Path(self.gen_dir)

    @contextmanager
    def phase(self, name: str):
        t0 = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - t0
            self.phases[name] = self.phases.get(name, 0.0) + elapsed
            self.phase_counts[name] = self.phase_counts.get(name, 0) + 1

    def add(self, name: str, seconds: float) -> None:
        """Manually add time to a phase (for code you can't wrap in a context manager)."""
        self.phases[name] = self.phases.get(name, 0.0) + float(seconds)
        self.phase_counts[name] = self.phase_counts.get(name, 0) + 1

    def write(self) -> Optional[Path]:
        """Dump timing.json; best-effort, returns the path on success."""
        if not self.enabled:
            return None
        try:
            self.gen_dir.mkdir(parents=True, exist_ok=True)
            total_wall = time.time() - self.start_ts
            payload = {
                "total_wall_secs": round(total_wall, 2),
                "phases": {
                    k: {"secs": round(v, 2),
                        "count": self.phase_counts.get(k, 0),
                        "pct_of_total": round(100 * v / total_wall, 1) if total_wall > 0 else 0.0}
                    for k, v in sorted(self.phases.items(), key=lambda kv: -kv[1])
                },
            }
            out_path = self.gen_dir / "timing.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            return out_path
        except Exception:
            return None


# ── Status heartbeat ─────────────────────────────────────────────

@dataclass
class StatusHeartbeat:
    """Writes a small JSON file (`status.json`) under the run directory each
    time the optimizer enters a new "phase" (init, breeding, fitness_eval,
    layer1, layer2, layer3, checkpoint, …).

    At crash time the file is the canonical answer to "what was it doing?":
    it records the current generation, individual, phase, PID, host, and a
    UTC timestamp of the last update. Writes are atomic (tmp + rename)
    and guarded — the heartbeat never raises.

    Typical usage:

        hb = StatusHeartbeat(run_dir=Path("outputs/run"), pid=os.getpid())
        hb.update(phase="init")
        hb.update(phase="fitness_eval", generation=1, individual_idx=0,
                  individual_parent="original")
        hb.update(phase="layer1", generation=1, context={"task": "enso_0017", "outcome": "fail"})
    """

    run_dir: Path
    pid: int
    enabled: bool = True

    def __post_init__(self) -> None:
        self.run_dir = Path(self.run_dir)
        self.path = self.run_dir / "status.json"
        try:
            self.run_dir.mkdir(parents=True, exist_ok=True)
            import platform
            self._host = platform.node()
            self._launched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        except Exception:
            self._host = "?"
            self._launched_at = ""

    def update(
        self,
        phase: str,
        generation: Optional[int] = None,
        individual_idx: Optional[int] = None,
        individual_parent: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> None:
        """Update the heartbeat. Never raises from its own I/O."""
        if not self.enabled:
            return
        try:
            payload = {
                "pid": self.pid,
                "host": self._host,
                "launched_at": self._launched_at,
                "last_update": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "phase": phase,
                "generation": generation,
                "individual_idx": individual_idx,
                "individual_parent": individual_parent,
                "context": context or {},
                "message": message,
            }
            tmp = self.path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            tmp.rename(self.path)
        except Exception:
            pass


# ── Telemetry-mode resolver ───────────────────────────────────────

VALID_MODES = {"debug", "prod"}


def resolve_telemetry_mode(config: dict) -> str:
    """Pick 'debug' or 'prod' from config.

    Precedence:
      1. telemetry.mode if set (new canonical form)
      2. telemetry.enabled fallback (legacy) — True → debug, False → prod
      3. default: debug (safer during development)
    """
    tele = config.get("telemetry") or {}
    mode = tele.get("mode")
    if mode in VALID_MODES:
        return mode
    # Legacy fallback
    if "enabled" in tele:
        return "debug" if tele.get("enabled") else "prod"
    return "debug"


def describe_mode(mode: str) -> str:
    """One-line human-readable summary of what this mode enables."""
    if mode == "debug":
        return ("per-call prompt/response text files, errors.jsonl, timing.json, "
                "Phoenix spans if configured")
    return "llm_calls.jsonl index only (no per-call text files)"
