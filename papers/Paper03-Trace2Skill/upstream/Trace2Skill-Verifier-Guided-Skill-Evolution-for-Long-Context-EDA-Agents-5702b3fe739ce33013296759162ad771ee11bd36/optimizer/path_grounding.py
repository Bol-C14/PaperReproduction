#!/usr/bin/env python3
"""Detect target-file grounding failures in CVDP rollouts.

The optimizer learns from rollout traces, but an LLM summarizer can blur a
concrete failure like "wrote rtl/foo.v while the task target was
project/src/foo.v" into generic advice about verification. This module keeps
that evidence deterministic and explicit so later oracle/mutator stages can
turn it into a stable skill rule.
"""

from __future__ import annotations

import json
import posixpath
import re
import shlex
from collections import Counter, defaultdict
from typing import Iterable


RTL_EXT_RE = re.compile(r"\.(?:svh?|vh?)$", re.IGNORECASE)
RTL_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./+-])"
    r"(?P<path>(?:(?:/code/|code/)[A-Za-z0-9_][A-Za-z0-9_./+@=-]*|"
    r"[A-Za-z0-9_][A-Za-z0-9_./+@=-]*)\.(?:svh?|vh?))"
    r"(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
MODULE_NAME_RE = r"[A-Za-z_][A-Za-z0-9_$]*"
ACTION_WORDS_RE = re.compile(
    r"\b(add|create|write|implement|modify|edit|fix|correct|complete|update|replace|repair)\b",
    re.IGNORECASE,
)
READ_ONLY_RE = re.compile(
    r"\b(read[- ]only|reference|documentation|docs?|testbench|tb|visible verification|verify|validation)\b",
    re.IGNORECASE,
)
MISSING_MODULE_RE = re.compile(
    rf"\b(?:instantiates?|expects?|requires?)\s+(?:the\s+)?`?(?P<module>{MODULE_NAME_RE})`?"
    rf"(?:\s+module)?(?P<context>.{{0,220}}?\b(?:missing|not implemented|undefined|not found|absent)\b)",
    re.IGNORECASE | re.DOTALL,
)
MODULE_NOT_IMPLEMENTED_RE = re.compile(
    rf"`?(?P<module>{MODULE_NAME_RE})`?\s+module(?P<context>.{{0,220}}?"
    rf"\b(?:missing|not implemented|undefined|not found|absent)\b)",
    re.IGNORECASE | re.DOTALL,
)


def normalize_path(path: object) -> str:
    """Normalize tool/task paths to /code-relative POSIX strings."""
    if path is None:
        return ""
    value = str(path).strip().strip("\"'`")
    value = value.replace("\\", "/")
    value = re.sub(r"^[\s:=(\[]+", "", value)
    value = re.sub(r"[\s,;:)\]}]+$", "", value)
    if value.startswith("/code/"):
        value = value[len("/code/"):]
    elif value.startswith("code/"):
        value = value[len("code/"):]
    elif value.startswith("./"):
        value = value[2:]
    if not value or value in {".", "/"}:
        return ""
    normalized = posixpath.normpath(value)
    if normalized == ".":
        return ""
    return normalized.lstrip("/")


def _dedupe(paths: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for path in paths:
        norm = normalize_path(path)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        result.append(norm)
    return result


def _parse_call_args(call: dict) -> dict:
    args_raw = call.get("arguments") or {}
    if isinstance(args_raw, dict):
        return args_raw
    if isinstance(args_raw, str):
        try:
            parsed = json.loads(args_raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _response_output_items(rollout: dict) -> list[dict]:
    response = rollout.get("response") or {}
    items = response.get("output") or []
    return [item for item in items if isinstance(item, dict)]


def _tool_calls(rollout: dict) -> list[dict]:
    return [
        item for item in _response_output_items(rollout)
        if item.get("type") == "function_call"
    ]


def extract_written_paths(rollout: dict) -> list[str]:
    paths = []
    for call in _tool_calls(rollout):
        if call.get("name") not in {"echo", "edit"}:
            continue
        args = _parse_call_args(call)
        paths.append(args.get("filename") or args.get("path") or "")
    return _dedupe(paths)


def _rtl_paths_from_command(command: object) -> list[str]:
    if command is None:
        return []
    text = " ".join(str(x) for x in command) if isinstance(command, list) else str(command)
    tokens: list[str]
    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = text.split()
    paths = []
    for token in tokens:
        for match in RTL_PATH_RE.finditer(token):
            paths.append(match.group("path"))
    return _dedupe(paths)


def extract_compiled_paths(rollout: dict) -> list[str]:
    paths = []
    for call in _tool_calls(rollout):
        if call.get("name") not in {"iverilog", "xcelium"}:
            continue
        args = _parse_call_args(call)
        paths.extend(_rtl_paths_from_command(args.get("args") or args.get("command") or ""))
    return _dedupe(paths)


def _input_text(input_obj: object) -> str:
    if isinstance(input_obj, str):
        return input_obj
    if isinstance(input_obj, dict):
        parts = []
        for key in ("content", "text", "prompt"):
            if key in input_obj:
                parts.append(_input_text(input_obj.get(key)))
        return "\n".join(part for part in parts if part)
    if isinstance(input_obj, list):
        return "\n".join(_input_text(item) for item in input_obj if item is not None)
    return ""


def extract_task_text(rollout: dict) -> str:
    """Return the user/developer task text embedded in a task or rollout row."""
    chunks = []
    for container in (
        rollout.get("responses_create_params"),
        rollout.get("task", {}),
        rollout,
    ):
        if isinstance(container, dict):
            chunks.append(_input_text(container.get("input")))
            chunks.append(_input_text(container.get("prompt")))
            chunks.append(_input_text(container.get("messages")))
    metadata = rollout.get("verifier_metadata") or {}
    if isinstance(metadata, dict):
        chunks.append(_input_text(metadata.get("prompt")))
        chunks.append(_input_text(metadata.get("task_description")))
    return "\n".join(chunk for chunk in chunks if chunk)


def _explicit_target_paths(task_text: str) -> list[str]:
    targets = []
    for match in RTL_PATH_RE.finditer(task_text):
        path = normalize_path(match.group("path"))
        if not path:
            continue
        prefix = task_text[max(0, match.start() - 90):match.start()]
        suffix = task_text[match.end():min(len(task_text), match.end() + 90)]
        if (
            re.search(r"\b(located at|defined in|found in|found at)\s+[`']?$", prefix, re.IGNORECASE)
            and re.search(r"\b(top[- ]level|instantiates?)\b", prefix + suffix, re.IGNORECASE)
        ):
            continue
        start = max(0, match.start() - 180)
        end = min(len(task_text), match.end() + 180)
        window = task_text[start:end]
        if ACTION_WORDS_RE.search(window):
            targets.append(path)
            continue
        # A source path named immediately before "is not implemented/missing"
        # is usually the file the agent must create or complete.
        if re.search(r"\b(missing|not implemented|undefined|not found|absent)\b", window, re.IGNORECASE):
            if not READ_ONLY_RE.search(window):
                targets.append(path)
    return _dedupe(targets)


def _nearest_existing_rtl_dir(task_text: str, module_match_start: int) -> str | None:
    candidates = []
    for path_match in RTL_PATH_RE.finditer(task_text):
        path = normalize_path(path_match.group("path"))
        if not path:
            continue
        distance = abs(path_match.start() - module_match_start)
        candidates.append((distance, path))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    parent = posixpath.dirname(candidates[0][1])
    return parent or None


def _missing_module_target_paths(task_text: str) -> list[str]:
    targets = []
    for regex in (MISSING_MODULE_RE, MODULE_NOT_IMPLEMENTED_RE):
        for match in regex.finditer(task_text):
            module = match.group("module")
            prefix = task_text[max(0, match.start() - 12):match.start()].lower()
            if not module or module.lower() in {"module", "design", "file", "level"}:
                continue
            if prefix.endswith("top-") or prefix.endswith("top "):
                continue
            parent = _nearest_existing_rtl_dir(task_text, match.start())
            if not parent:
                continue
            ext = ".sv" if any(
                normalize_path(p.group("path")).endswith(".sv")
                for p in RTL_PATH_RE.finditer(task_text)
            ) else ".v"
            targets.append(f"{parent}/{module}{ext}")
    return _dedupe(targets)


def infer_expected_target_paths(rollout_or_task: dict) -> list[str]:
    """Infer the RTL file(s) the agent is expected to write/edit."""
    task_text = extract_task_text(rollout_or_task)
    targets = _explicit_target_paths(task_text)
    inferred = _missing_module_target_paths(task_text)
    return _dedupe([*targets, *inferred])


def _basename(path: str) -> str:
    return posixpath.basename(normalize_path(path))


def _paths_with_basename(paths: Iterable[str], basename: str, expected: str) -> list[str]:
    expected_norm = normalize_path(expected)
    return [
        path for path in _dedupe(paths)
        if _basename(path) == basename and normalize_path(path) != expected_norm
    ]


def analyze_path_grounding(
    rollout: dict,
    *,
    files_written: list[str] | None = None,
    compile_commands: list[str] | None = None,
    reward: float | None = None,
) -> dict:
    """Compare expected target files against rollout writes/compiles."""
    expected = infer_expected_target_paths(rollout)
    written = _dedupe(files_written if files_written is not None else extract_written_paths(rollout))
    if compile_commands is None:
        compiled = extract_compiled_paths(rollout)
    else:
        compiled = _dedupe(
            path
            for command in compile_commands
            for path in _rtl_paths_from_command(command)
        )
    reward_value = float(rollout.get("reward", 0.0) if reward is None else reward or 0.0)

    issues = []
    directives = []
    for target in expected:
        basename = _basename(target)
        if not basename:
            continue
        wrote_target = target in written
        compiled_target = target in compiled
        wrong_writes = _paths_with_basename(written, basename, target)
        wrong_compiles = _paths_with_basename(compiled, basename, target)

        if wrong_writes and not wrote_target:
            issues.append({
                "code": "wrong_target_path",
                "severity": "critical" if reward_value <= 0 else "warning",
                "expected": target,
                "observed": wrong_writes,
                "summary": (
                    f"Expected writes to {target}, but rollout wrote same-basename "
                    f"path(s): {', '.join(wrong_writes)}"
                ),
            })
        elif wrong_writes and wrote_target:
            issues.append({
                "code": "shadow_target_path",
                "severity": "warning",
                "expected": target,
                "observed": wrong_writes,
                "summary": (
                    f"Rollout wrote the expected target {target} and also shadow "
                    f"same-basename path(s): {', '.join(wrong_writes)}"
                ),
            })
        elif not wrote_target and written:
            issues.append({
                "code": "missing_expected_write",
                "severity": "critical" if reward_value <= 0 else "warning",
                "expected": target,
                "observed": written[:10],
                "summary": f"Rollout wrote files but did not write/edit expected target {target}",
            })

        if wrong_compiles and not compiled_target:
            issues.append({
                "code": "validation_on_wrong_path",
                "severity": "critical" if reward_value <= 0 else "warning",
                "expected": target,
                "observed": wrong_compiles,
                "summary": (
                    f"Local compile/validation used same-basename path(s) "
                    f"{', '.join(wrong_compiles)} but not expected target {target}"
                ),
            })

        if wrong_writes or wrong_compiles or (written and not wrote_target):
            observed = _dedupe([*wrong_writes, *wrong_compiles])
            if observed:
                directives.append(
                    f"Use the prompt-discovered target path `{target}`; do not write or validate "
                    f"only same-basename shadow paths such as `{observed[0]}`."
                )
            else:
                directives.append(
                    f"Before declaring done, write/edit the actual target file `{target}` and "
                    "include it in visible local compile checks."
                )

    issue_codes = [issue["code"] for issue in issues]
    return {
        "expected_targets": expected[:20],
        "written_paths": written[:40],
        "compiled_paths": compiled[:40],
        "issues": issues,
        "issue_codes": issue_codes,
        "has_issues": bool(issues),
        "has_critical_issue": any(issue.get("severity") == "critical" for issue in issues),
        "hard_directives": _dedupe(directives)[:10],
    }


def format_path_grounding_for_oracle(rollout: dict) -> str:
    """Render path-grounding evidence for Layer-1 task insight refinement."""
    analysis = analyze_path_grounding(rollout)
    if not analysis.get("expected_targets") and not analysis.get("issues"):
        return ""
    lines = [
        "PATH_GROUNDING_CHECK:",
        f"  Expected target(s): {', '.join(analysis['expected_targets']) or '(not inferred)'}",
        f"  Files written: {', '.join(analysis['written_paths']) or '(none)'}",
        f"  RTL paths compiled: {', '.join(analysis['compiled_paths']) or '(none)'}",
    ]
    if analysis.get("issues"):
        lines.append("  Issues:")
        for issue in analysis["issues"][:6]:
            lines.append(
                f"    - [{issue['severity']}] {issue['code']}: {issue['summary']}"
            )
    if analysis.get("hard_directives"):
        lines.append("  Protected path directive(s):")
        for directive in analysis["hard_directives"][:4]:
            lines.append(f"    - {directive}")
    return "\n".join(lines)


def summarize_path_grounding_diagnostics(diagnostics: list[dict]) -> dict:
    """Aggregate path-grounding issues for generation_metrics.json."""
    issue_counter: Counter[str] = Counter()
    severity_counter: Counter[str] = Counter()
    by_task: dict[str, Counter[str]] = defaultdict(Counter)
    by_cid: dict[str, Counter[str]] = defaultdict(Counter)
    examples = []

    for diag in diagnostics:
        grounding = diag.get("path_grounding") or {}
        for issue in grounding.get("issues") or []:
            code = str(issue.get("code") or "unknown")
            severity = str(issue.get("severity") or "unknown")
            issue_counter[code] += 1
            severity_counter[severity] += 1
            by_task[str(diag.get("short_task_id") or diag.get("task_id") or "unknown")][code] += 1
            by_cid[str(diag.get("cid") or "unknown")][code] += 1
            if len(examples) < 8:
                examples.append({
                    "rollout_id": diag.get("rollout_id"),
                    "task": diag.get("short_task_id") or diag.get("task_id"),
                    "cid": diag.get("cid"),
                    "code": code,
                    "severity": severity,
                    "expected": issue.get("expected"),
                    "observed": issue.get("observed"),
                })

    return {
        "issue_count": sum(issue_counter.values()),
        "by_code": dict(sorted(issue_counter.items())),
        "by_severity": dict(sorted(severity_counter.items())),
        "by_task": {task: dict(counter) for task, counter in sorted(by_task.items())},
        "by_cid": {cid: dict(counter) for cid, counter in sorted(by_cid.items())},
        "examples": examples,
    }
