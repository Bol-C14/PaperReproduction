"""Post-mutation processing for Trace2Skill evolved skills.

The genetic optimizer intentionally lets the mutator explore: it can add new
rules, reframe old ones, and compress oracle feedback into a next-generation
skill. That raw LLM output is *not* what we want to inject directly into future
rollouts. Before handoff, the skill needs a deterministic processing layer that
does four jobs:

1. Ground the skill in the rollout agent's real execution contract.
2. Remove impossible, contradictory, or hidden-verifier-only instructions.
3. Keep growth bounded so useful guidance is consolidated instead of diluted.
4. Record machine-readable health telemetry when mutation silently fails.

This file is therefore the single home for the "raw mutated skill -> injectable
next-generation skill" path. The optimizer loop should call into this module
instead of reimplementing post-mutation cleanup, validation, and logging.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from difflib import unified_diff
from difflib import SequenceMatcher
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Iterable


DEFAULT_ALLOWED_TOOLS = (
    "ls",
    "cat",
    "rg",
    "find_files",
    "read_file",
    "show_changes",
    "module_index",
    "echo",
    "edit",
    "iverilog",
    "vvp",
    "pwd",
)

SHELL_OR_EXTERNAL_COMMANDS = (
    "bash",
    "sh",
    "shell",
    "grep",
    "sed",
    "awk",
    "tail",
    "head",
    "wc",
    "find",
    "git",
    "make",
    "pytest",
    "python",
    "docker",
    "cp",
    "mv",
    "rm",
    "diff",
    "tee",
)


class MutationValidationError(RuntimeError):
    """Raised when post-mutation processing rejects a candidate skill."""


@dataclass(frozen=True)
class SkillExecutionContract:
    """What the rollout agent can and cannot do."""

    allowed_tools: tuple[str, ...] = DEFAULT_ALLOWED_TOOLS
    visible_context_paths: tuple[str, ...] = ()
    hidden_verifier: bool = True
    can_run_official_harness: bool = False
    may_modify_testbench: bool = False
    task_type: str = "rtl_or_design"
    write_tool: str = "echo"
    task_prompt_excerpt: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SanitizationResult:
    text: str
    ok: bool
    issues: list[str]
    warnings: list[str]
    metrics: dict

    def to_record(self) -> dict:
        return {
            "ok": self.ok,
            "issues": self.issues,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


@dataclass
class FeedbackSanitizationResult:
    """Result from sanitizing oracle/mutation handoff prose.

    This is deliberately lighter-weight than `sanitize_skill`: oracle feedback
    and mutation handoffs are diagnostic artifacts, not injected skills. The
    invariant here is narrower but critical: text that reaches the mutator must
    not ask the rollout agent to run unavailable harnesses, shells, pytest,
    make, docker, or hidden verifier machinery.
    """

    text: str
    changed: bool
    issues: list[str]
    rewrites: list[dict]
    metrics: dict

    def to_record(self) -> dict:
        return {
            "changed": self.changed,
            "issues": self.issues,
            "rewrites": self.rewrites,
            "metrics": self.metrics,
        }


def _json_safe(obj):
    """Return an object that json.dump/json.dumps can serialize."""
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [_json_safe(v) for v in obj]
    return obj


def _write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_json_safe(data), f, indent=2, ensure_ascii=False)


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                rows.append(rec)
    return rows


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _iter_prompt_messages(tasks: Iterable[dict]) -> Iterable[str]:
    for task in tasks:
        params = task.get("responses_create_params") or {}
        for msg in params.get("input") or []:
            if isinstance(msg, dict):
                content = msg.get("content")
                if isinstance(content, str):
                    yield content


def _extract_tools_from_schema(tasks: Iterable[dict]) -> tuple[str, ...]:
    """Extract declared function tools from responses_create_params.tools."""
    ordered: list[str] = []
    seen: set[str] = set()
    for task in tasks:
        params = task.get("responses_create_params") or {}
        tools = params.get("tools") or []
        if not isinstance(tools, list):
            continue
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            name = tool.get("name")
            if not isinstance(name, str) or not name or name in seen:
                continue
            seen.add(name)
            ordered.append(name)
    return tuple(ordered)


def _extract_tools_from_text(text: str) -> tuple[str, ...]:
    """Extract tool names from a developer prompt's TOOLS section."""
    match = re.search(
        r"TOOLS\b.*?(?=\n\s*\n[A-Z][A-Z _-]{3,}:|\n\s*\nREQUIRED FLOW|\n\s*\nStep\s+1|\Z)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    section = match.group(0) if match else text
    tools = re.findall(r"(?m)^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", section)
    # Keep first-seen order and ignore prose words accidentally matched later.
    seen: set[str] = set()
    ordered: list[str] = []
    for tool in tools:
        name = tool.strip()
        if name and name not in seen:
            seen.add(name)
            ordered.append(name)
    return tuple(ordered)


def _normalize_context_path(path: str) -> str:
    """Normalize CVDP-visible paths for deterministic skill grounding checks."""
    text = str(path or "").strip().strip("`'\"")
    text = re.sub(r"^[.]/+", "", text)
    text = re.sub(r"^/code/+", "", text)
    text = re.sub(r"/+", "/", text)
    return text.strip("/")


def _extract_visible_context_paths(tasks: Iterable[dict]) -> tuple[str, ...]:
    """Return files visible to the rollout agent from verifier metadata.

    CVDP stores hidden harness files separately from `context_files`; only the
    latter are materialized into the agent's `/code` workspace. The sanitizer
    uses this list to avoid turning oracle observations into impossible next-gen
    skill directives such as "read /code/verif tests" when that directory only
    contains `.gitkeep`.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for task in tasks:
        metadata = task.get("verifier_metadata") or {}
        context_files = metadata.get("context_files") or {}
        if not isinstance(context_files, dict):
            continue
        for raw_path in context_files.keys():
            path = _normalize_context_path(raw_path)
            if path and path not in seen:
                seen.add(path)
                ordered.append(path)
    return tuple(ordered)


def infer_execution_contract(tasks: list[dict]) -> SkillExecutionContract:
    """Infer the concrete rollout tool contract from task messages."""
    schema_allowed = _extract_tools_from_schema(tasks)
    prompt_texts = list(_iter_prompt_messages(tasks))
    visible_context_paths = _extract_visible_context_paths(tasks)
    allowed: tuple[str, ...] | None = None
    excerpt = ""
    for text in prompt_texts:
        if "TOOLS" not in text.upper():
            continue
        tools = _extract_tools_from_text(text)
        if tools:
            allowed = tools
            excerpt = text[:2500]
            break

    joined = "\n".join(prompt_texts).lower()
    hidden_verifier = (
        "hidden test harness" in joined
        or "hidden verifier" in joined
        or "grading:" in joined
        or "after you finish" in joined
    )
    # Visible testbenches are sometimes references and sometimes the requested
    # deliverable. Keep this distinction explicit so the sanitizer does not
    # inject a one-size-fits-all "never edit testbench" rule into CIDs whose
    # whole job is verification/testbench construction.
    may_modify_testbench = bool(re.search(
        r"\b(?:write|create|implement|build|generate|modify|edit|fix)\b.{0,80}"
        r"\b(?:testbench|test bench|tb|verification|checker|assertion|sva|property)\b",
        joined,
        flags=re.IGNORECASE | re.DOTALL,
    ))
    task_type = "testbench_or_verification" if may_modify_testbench else "rtl_or_design"
    allowed_tools = schema_allowed or allowed or DEFAULT_ALLOWED_TOOLS
    return SkillExecutionContract(
        allowed_tools=allowed_tools,
        visible_context_paths=visible_context_paths,
        hidden_verifier=hidden_verifier,
        can_run_official_harness=False if hidden_verifier else "pytest" in allowed_tools,
        may_modify_testbench=may_modify_testbench,
        task_type=task_type,
        write_tool="edit" if "edit" in allowed_tools else "echo",
        task_prompt_excerpt=excerpt,
    )


def build_execution_constraints_text(contract: SkillExecutionContract) -> str:
    tools = ", ".join(f"{tool}(...)" for tool in contract.allowed_tools)
    unavailable = [cmd for cmd in SHELL_OR_EXTERNAL_COMMANDS if cmd not in contract.allowed_tools]
    if "edit" not in contract.allowed_tools:
        unavailable.append("edit")
    if "xcelium" not in contract.allowed_tools:
        unavailable.append("xcelium")
    if "restore_file" not in contract.allowed_tools:
        unavailable.append("restore_file")

    lines = [
        "ROLLOUT EXECUTION CONTRACT:",
        f"- The rollout agent can call only these tools: {tools}.",
        "- Do not put unavailable commands, shell snippets, pipes, redirection, or external tooling in the skill.",
        f"- Unavailable actions/tools include: {', '.join(sorted(set(unavailable)))}.",
        "- Do not require a concrete path, test directory, or verification file unless it is visible in the task context or the agent can discover it with allowed file-inspection tools.",
    ]
    if contract.hidden_verifier:
        lines.extend([
            "- The external verifier is unavailable during rollout and runs only after the rollout.",
            "- The skill may tell the agent to READ visible specs and task-relevant visible .v/.sv verification files.",
            "- The skill must NOT tell the agent to run the official harness, pytest, make, docker, or any hidden verifier.",
            "- For self-checking, use only visible RTL/SystemVerilog files with the allowed simulator tools.",
        ])
    if contract.may_modify_testbench:
        lines.append(
            "- The task prompt appears to request testbench/verification work; visible testbench/checker files may be created or edited only as requested deliverables."
        )
    else:
        lines.append(
            "- Treat visible testbench/checker/verification files as read-only references unless the task explicitly names them as deliverables."
        )
    if "echo" in contract.allowed_tools and "edit" not in contract.allowed_tools:
        lines.append(
            "- File writes must use echo(content, filename), which overwrites the complete file; do not recommend edit()."
        )
    elif "edit" in contract.allowed_tools:
        lines.append("- Prefer edit() for surgical changes and echo() only for brand-new files.")
    return "\n".join(lines)


def skill_length_budget(parent_text: str, max_chars: int, sanitizer_cfg: dict | None = None) -> int:
    """Return the mutator-facing child skill length budget.

    The budget is a consolidation target, not the only line of defense. Tiny
    seed skills need room to absorb real oracle insight, so the floor is a
    usable-skill minimum instead of a direct function of parent length.
    """
    cfg = sanitizer_cfg or {}
    parent_len = len(parent_text or "")
    if not cfg.get("enabled", True):
        return max_chars if max_chars > 0 else 0
    ratio = float(cfg.get("max_growth_ratio", 1.35))
    growth_chars = int(cfg.get("max_growth_chars", 2000))
    floor = int(cfg.get("min_budget_chars", 3500))
    if parent_len < floor:
        budget = floor
    else:
        budget = max(floor, min(int(parent_len * ratio), parent_len + growth_chars))
    if max_chars > 0:
        return min(max(budget, floor), max_chars)
    return max(budget, floor)


def _whole_document_unfence(text: str) -> tuple[str, bool]:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text, False
    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip() + "\n", True
    return text, False


def _is_negative_instruction(lower: str) -> bool:
    return any(
        marker in lower
        for marker in (
            "do not ",
            "don't ",
            "never ",
            "cannot ",
            "can't ",
            "not available",
            "unavailable",
            "instead of",
            "rather than",
            "no ",
            "avoid ",
            "without ",
            "forbid",
            "forbidden",
            "must not ",
        )
    )


def _mentions_command(line: str, command: str) -> bool:
    """Return whether a line appears to invoke an unavailable command.

    This is intentionally stricter than a bare word match. We want to catch
    actual command-like instructions such as `find ...`, find(...), "run find",
    or shell snippets, without rejecting ordinary English like "Find DUT top" or
    "confirm diff" in a skill.
    """
    escaped = re.escape(command)
    stripped = line.strip()
    without_bullet = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", stripped)
    lower = without_bullet.lower()

    if re.search(rf"`\s*{escaped}(?:\s|$|[(/-])", line, re.IGNORECASE):
        return True
    if re.search(rf"(?<![A-Za-z0-9_]){escaped}\s*\(", line, re.IGNORECASE):
        return True
    if re.match(rf"^{escaped}(?:\s|$|[./-])", without_bullet):
        # Lowercase command at the start of an instruction is shell-like; Title
        # Case "Find ..." is usually English prose.
        return without_bullet[: len(command)] == command
    if re.search(rf"\b(?:run|execute|invoke|call|use|launch|pipe to|shell out to)\s+{escaped}\b", lower):
        return True
    return False


def _mentions_hidden_verifier_action(lower: str) -> bool:
    hidden_target = (
        "hidden harness" in lower
        or "official harness" in lower
        or "hidden verifier" in lower
        or "official verifier" in lower
        or "hidden tests" in lower
    )
    if not hidden_target:
        return False
    return any(
        word in lower
        for word in (
            "run",
            "execute",
            "invoke",
            "call",
            "launch",
            "use",
            "verify",
            "validate",
            "rely",
            "authoritative",
            "pytest",
            "test_runner",
        )
    )


def _mentions_harness_execution_action(lower: str) -> bool:
    """Return whether prose tells the rollout to execute a harness-like flow.

    This intentionally excludes read/inspect/parse guidance. The rollout agent
    can use visible harness artifacts as metadata, but hidden/official harness
    execution is outside its contract and should not survive into an injected
    skill as an action directive.
    """
    return bool(
        re.search(
            r"\b(run|execute|invoke|launch|re-run|rerun|validate|verify)\b"
            r".{0,90}\b(?:hidden|official|repository|repo|provided|visible)?\s*"
            r"(?:harness|verifier|test[_ -]?runner|test suite)\b",
            lower,
        )
        or re.search(
            r"\b(?:harness|verifier|test[_ -]?runner|test suite)\b"
            r".{0,90}\b(run|execute|invoke|launch|re-run|rerun|validate|verify)\b",
            lower,
        )
    )


def _requests_testbench_modification(lower: str) -> bool:
    """Return whether a line positively asks to edit visible verification files.

    Phrases such as "edit-validate loop" or "make an edit, then read the
    testbench" are good rollout guidance and should not be treated as a request
    to modify the testbench itself. This helper is intentionally narrower than
    the old proximity regex so feedback diagnostics do not create false alarms.
    """
    if _is_negative_instruction(lower):
        return False
    scrubbed = re.sub(r"\bedit\s*[-–]\s*validate\b", "validate", lower)
    testbench = r"(?:testbench|test bench|tb|verification|verif|checker)"
    qualifier = r"(?:(?:the\s+)?(?:provided|visible|existing|project)\s+)?"
    return bool(
        re.search(rf"\b(?:edit|modify|overwrite)\b\s+{qualifier}{testbench}\b", scrubbed)
        or re.search(rf"\b{testbench}\b.{0,40}\b(?:edit|modify|overwrite)\b", scrubbed)
    )


PATH_TOKEN_RE = re.compile(
    r"(?:`([^`]*(?:/code/|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-])[^`]*)`)"
    r"|(?<![A-Za-z0-9_])(/code/[A-Za-z0-9_./+-]+)"
    r"|(?<![A-Za-z0-9_])((?:[A-Za-z0-9_.-]+/){1,}[A-Za-z0-9_.+-]+)"
)

PLACEHOLDER_VISIBLE_FILES = {".gitkeep", ".keep", "README", "README.md"}
TESTLIKE_PATH_PARTS = (
    "verif",
    "verification",
    "test",
    "tests",
    "tb",
    "testbench",
    "checker",
    "assert",
)
TESTLIKE_SUFFIXES = (
    ".v",
    ".sv",
    ".svh",
    ".vh",
    ".py",
    ".f",
    ".flist",
    ".list",
    ".tcl",
)


def _extract_path_references(line: str) -> list[str]:
    refs: list[str] = []
    for match in PATH_TOKEN_RE.finditer(line):
        raw = next((g for g in match.groups() if g), "")
        path = _normalize_context_path(raw.rstrip(".,;:)"))
        if path and path not in refs:
            refs.append(path)
    return refs


def _visible_dirs(paths: Iterable[str]) -> set[str]:
    dirs: set[str] = set()
    for path in paths:
        parts = _normalize_context_path(path).split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]))
    return dirs


def _path_or_parent_visible(path: str, contract: SkillExecutionContract) -> bool:
    visible = set(contract.visible_context_paths)
    dirs = _visible_dirs(visible)
    norm = _normalize_context_path(path)
    if not norm:
        return True
    if norm in visible or norm in dirs:
        return True
    parent = norm.rsplit("/", 1)[0] if "/" in norm else ""
    return bool(parent and parent in dirs)


def _visible_children(path: str, contract: SkillExecutionContract) -> list[str]:
    norm = _normalize_context_path(path)
    prefix = f"{norm}/" if norm else ""
    return [p for p in contract.visible_context_paths if p.startswith(prefix)]


def _path_has_task_relevant_tests(path: str, contract: SkillExecutionContract) -> bool:
    children = _visible_children(path, contract)
    if not children:
        return False
    for child in children:
        name = child.rsplit("/", 1)[-1]
        if name in PLACEHOLDER_VISIBLE_FILES:
            continue
        lower = child.lower()
        if any(part in lower for part in TESTLIKE_PATH_PARTS) or lower.endswith(TESTLIKE_SUFFIXES):
            return True
    return False


def _line_requests_path_reading(lower: str) -> bool:
    return bool(re.search(r"\b(read|open|inspect|cat|check|look at|use|parse)\b", lower))


def _line_requests_path_creation(lower: str) -> bool:
    return bool(re.search(r"\b(write|create|implement|add|generate|edit|modify|produce)\b", lower))


def _line_is_testlike(lower: str) -> bool:
    return any(part in lower for part in TESTLIKE_PATH_PARTS) or bool(
        re.search(r"\b(test|tests|testbench|verif|verification|checker|assertion|harness)\b", lower)
    )


def _ground_visible_path_line(
    line: str,
    contract: SkillExecutionContract,
    issues: list[str],
) -> str:
    """Rewrite positive path directives that are not grounded in visible files.

    This is intentionally a validator/rewriter rather than a hard reject. The
    mutator may discover a useful lesson but phrase it as if every task has the
    same visible tests. We keep the lesson while making it conditional on what
    the rollout agent can actually see.
    """
    if not contract.visible_context_paths:
        return line
    lower = line.lower()
    if _is_negative_instruction(lower):
        return line
    refs = _extract_path_references(line)
    if not refs:
        return line

    for ref in refs:
        norm = _normalize_context_path(ref)
        if not norm:
            continue

        # Visible test/checker directories that only contain placeholders are a
        # common source of hallucinated skill advice. Preserve the high-level
        # lesson but force discovery before reliance.
        if _line_is_testlike(lower) and _line_requests_path_reading(lower):
            if norm in _visible_dirs(contract.visible_context_paths) and not _path_has_task_relevant_tests(norm, contract):
                issues.append("rewrote_unavailable_visible_test_path")
                return (
                    "- Check whether task-relevant visible test, verification, or checker files actually exist before relying on them; "
                    "if those directories only contain placeholders, use visible specs/RTL and allowed simulator self-checks instead."
                )

        if _path_or_parent_visible(norm, contract):
            continue

        if _line_requests_path_creation(lower):
            # Creating a new file in a discovered parent directory is often the
            # actual task. Do not block that pattern unless even the parent is
            # ungrounded.
            parent = norm.rsplit("/", 1)[0] if "/" in norm else ""
            if parent and _path_or_parent_visible(parent, contract):
                continue

        if _line_requests_path_reading(lower):
            issues.append("rewrote_unconfirmed_path_guidance")
            return (
                "- Resolve concrete paths from visible ls/find_files/rg output before relying on them; "
                "do not require a path or file until the agent has confirmed it exists."
            )

    return line


def _replace_or_drop_impossible_line(
    line: str,
    contract: SkillExecutionContract,
    issues: list[str],
) -> str | None:
    lower = line.lower()
    allowed = set(contract.allowed_tools)

    if not contract.can_run_official_harness and not _is_negative_instruction(lower):
        if _mentions_hidden_verifier_action(lower):
            issues.append("removed_impossible_harness_run")
            return (
                "- Read visible specs and task-relevant visible .v/.sv verification files if present, "
                "but self-check only with allowed simulator tools."
            )
        if _mentions_harness_execution_action(lower):
            issues.append("rewrote_harness_execution_to_visible_metadata")
            return (
                "- Read visible specs, testbenches, filelists, and harness metadata if present; "
                "use them as references while self-checking only with allowed simulator tools."
            )

    if "pytest" in lower or "test runner" in lower:
        if not _is_negative_instruction(lower):
            issues.append("removed_impossible_pytest_or_test_runner")
            return None

    if "edit" not in allowed and _mentions_command(line, "edit"):
        issues.append("removed_unavailable_edit_tool")
        return "- Use echo(content, filename) for complete-file writes, then cat(filename=...) to inspect the result."

    if not contract.may_modify_testbench and _requests_testbench_modification(lower):
        issues.append("rewrote_testbench_modification_without_task_request")
        return (
            "- Read visible testbench/checker files as references; edit them only when the task explicitly requests a verification deliverable."
        )

    for tool in ("xcelium", "restore_file"):
        if tool not in allowed and _mentions_command(line, tool) and not _is_negative_instruction(lower):
            issues.append(f"removed_unavailable_{tool}")
            return None

    for command in SHELL_OR_EXTERNAL_COMMANDS:
        if command in allowed:
            continue
        if _mentions_command(line, command) and not _is_negative_instruction(lower):
            issues.append(f"removed_unavailable_command:{command}")
            return None

    if re.search(r"\s(?:&&|\|\||\||>|<)\s", line) and not _is_negative_instruction(lower):
        issues.append("removed_shell_syntax")
        return None

    line = _ground_visible_path_line(line, contract, issues)
    return line


def _line_has_positive_action(lower: str) -> bool:
    return bool(re.search(
        r"\b(run|execute|invoke|launch|re-run|rerun|use|validate|verify|call|try|prefer|always|must|edit|modify|overwrite)\b",
        lower,
    ))


def _feedback_replacement_for_unavailable_action(
    line: str,
    contract: SkillExecutionContract,
) -> tuple[str | None, str | None]:
    """Return a safe replacement for one oracle/mutation handoff line.

    The oracle is allowed to discuss hidden verifier failures as evidence. It
    is not allowed to turn that evidence into a next-generation skill directive
    that the rollout agent cannot execute. This keeps diagnostics rich while
    making the mutator's input obey the same execution contract as skills.
    """
    lower = line.lower()
    if not line.strip() or _is_negative_instruction(lower):
        return line, None

    allowed = set(contract.allowed_tools)
    positive = _line_has_positive_action(lower)
    if not positive:
        return line, None
    if "verify_feedback" in allowed and _mentions_command(line, "verify_feedback"):
        # The dense-feedback branch exposes a budgeted black-box verifier tool.
        # Treat that tool as allowed while the usual hidden-harness ban still
        # applies to paths, raw logs, docker, pytest, and harness internals.
        return line, None

    harness_like = (
        re.search(r"\b(run|execute|invoke|launch|re-run|rerun|use|validate|verify)\b.{0,90}\b(?:hidden|official|repository|repo|provided|visible)?\s*(?:harness|verifier|test[_ -]?runner|test suite)\b", lower)
        or re.search(r"\b(?:harness|verifier|test[_ -]?runner|test suite)\b.{0,90}\b(?:run|execute|invoke|launch|re-run|rerun|validate|verify)\b", lower)
    )
    if not contract.can_run_official_harness and harness_like:
        return (
            "- Read visible specs, testbenches, filelists, and harness metadata if present; "
            "self-check only with available rollout tools and do not tell the agent to run hidden or official harnesses "
            "or unavailable commands such as pytest, make, or docker.",
            "rewrite_unavailable_harness_run",
        )

    unavailable_commands = []
    for command in ("pytest", "docker", "make", "python", "bash", "sh", "git"):
        if command in allowed:
            continue
        if _mentions_command(line, command):
            # Reading a Makefile as a file is okay; running make is not.
            if command == "make" and re.search(r"\b(read|open|inspect)\b.{0,50}\bmakefiles?\b", lower):
                continue
            unavailable_commands.append(command)
    if unavailable_commands:
        return (
            "- Read visible repository test/build metadata as references, then reproduce checks with allowed simulator tools "
            f"({', '.join(contract.allowed_tools)}); do not require unavailable commands such as {', '.join(sorted(unavailable_commands))}.",
            "rewrite_unavailable_command_guidance",
        )

    if re.search(r"\b(xrun|xcelium)\b", lower):
        if "xcelium" not in allowed:
            return (
                "- Use only available simulator tools from the rollout contract; prefer iverilog/vvp for local self-checks.",
                "rewrite_unavailable_xcelium_guidance",
            )
        if re.search(r"\b(always|must|use|prefer|invoke|run|execute)\b", lower):
            return (
                "- Use xcelium only after confirming the tool is available in the rollout environment; otherwise use iverilog/vvp.",
                "make_xcelium_guidance_conditional",
            )

    if re.search(r"\s(?:&&|\|\||\||>|<)\s", line):
        return (
            "- Use one allowed rollout tool call at a time; avoid shell pipelines, redirection, and compound shell snippets.",
            "rewrite_shell_syntax_guidance",
        )

    if not contract.may_modify_testbench and _requests_testbench_modification(lower):
        return (
            "- Read visible testbench/checker files as references; edit them only when the task explicitly requests a verification deliverable.",
            "rewrite_testbench_modification_without_task_request",
        )

    return line, None


def sanitize_feedback_for_execution_contract(
    text: str,
    contract: SkillExecutionContract,
    *,
    source: str = "mutation_feedback",
) -> FeedbackSanitizationResult:
    """Sanitize oracle feedback before it is handed to the skill mutator.

    This is a post-oracle, pre-mutator guardrail. It preserves diagnostic
    evidence, path-grounding directives, and visible-file reading guidance, but
    rewrites or removes positive instructions that would be impossible for the
    rollout agent to follow.
    """
    lines = (text or "").splitlines()
    rewrites: list[dict] = []
    sanitized_lines: list[str] = []
    issues: list[str] = []
    in_fence = False

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            sanitized_lines.append(line)
            continue
        if in_fence:
            sanitized_lines.append(line)
            continue

        replacement, reason = _feedback_replacement_for_unavailable_action(line, contract)
        if reason is None:
            sanitized_lines.append(line)
            continue

        issues.append(reason)
        rewrites.append({
            "line": idx,
            "reason": reason,
            "original": line[:300],
            "replacement": replacement[:300] if replacement is not None else None,
        })
        if replacement is not None:
            sanitized_lines.append(replacement)

    sanitized = "\n".join(sanitized_lines).strip()
    if sanitized:
        sanitized += "\n"
    remaining = _scan_remaining_impossible(sanitized, contract)
    return FeedbackSanitizationResult(
        text=sanitized,
        changed=bool(rewrites),
        issues=sorted(set(issues + remaining)),
        rewrites=rewrites,
        metrics={
            "source": source,
            "input_chars": len(text or ""),
            "output_chars": len(sanitized),
            "num_lines": len(lines),
            "num_rewrites": len(rewrites),
            "remaining_impossible": remaining,
            "allowed_tools": list(contract.allowed_tools),
            "hidden_verifier": contract.hidden_verifier,
            "can_run_official_harness": contract.can_run_official_harness,
        },
    )


def _hard_rules_section(contract: SkillExecutionContract) -> str:
    tools = ", ".join(contract.allowed_tools)
    rules = [
        f"Use only the rollout tools that exist here: {tools}.",
        "Text-only answers are ignored; write the required file(s) before stopping.",
        "Read visible specs and task-relevant visible .v/.sv verification files before writing.",
        "Verify with allowed simulator tools only: compile, then run simulation when a runnable sim is available.",
        "Keep build scope minimal; do not compile board/vendor/example IP unless the task explicitly requires it.",
    ]
    if contract.may_modify_testbench:
        rules.append("Because this is verification/testbench work, create or edit visible testbench/checker deliverables only when the task asks for them.")
    else:
        rules.append("Treat visible testbench/checker files as read-only references unless the task explicitly asks you to produce them.")
    if "echo" in contract.allowed_tools and "edit" not in contract.allowed_tools:
        rules.append("Use echo as a complete-file overwrite and cat the file afterward to inspect it.")
    elif "edit" in contract.allowed_tools:
        rules.append("Prefer edit for surgical changes to existing files; use echo for brand-new files or complete rewrites.")
    return "## Hard Rules\n\n" + "\n".join(f"- {rule}" for rule in rules)


def _ensure_hard_rules(text: str, contract: SkillExecutionContract, issues: list[str]) -> str:
    if re.search(r"(?mi)^##\s+Hard Rules\b", text):
        return text
    issues.append("inserted_missing_hard_rules")
    lines = text.splitlines()
    section = _hard_rules_section(contract).splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join([lines[0], "", *section, "", *lines[1:]]).strip() + "\n"
    return "\n".join([*section, "", text.strip()]).strip() + "\n"


def _low_actionability_warnings(text: str) -> list[str]:
    warnings = []
    vague_lines = 0
    for line in text.splitlines():
        stripped = line.strip().lower()
        if not stripped or stripped.startswith("#"):
            continue
        if any(phrase in stripped for phrase in ("consider ", "be mindful", "where possible", "as needed", "if appropriate")):
            vague_lines += 1
    if vague_lines >= 4:
        warnings.append(f"low_actionability_vague_lines:{vague_lines}")
    return warnings


def _scan_remaining_impossible(text: str, contract: SkillExecutionContract) -> list[str]:
    issues: list[str] = []
    allowed = set(contract.allowed_tools)
    lowered = text.lower()
    if "edit" not in allowed and re.search(r"\bedit\s*\(", lowered):
        issues.append("remaining_unavailable_edit_tool")
    if contract.hidden_verifier:
        harness_lines = [
            ln.lower()
            for ln in text.splitlines()
            if re.search(r"\b(run|execute|invoke|launch|re-run)\b.{0,50}\bharness\b", ln.lower())
        ]
        if any(not _is_negative_instruction(ln) for ln in harness_lines):
            issues.append("remaining_impossible_harness_run")
    for command in SHELL_OR_EXTERNAL_COMMANDS:
        if command in allowed:
            continue
        if re.search(rf"(?<![a-z0-9_]){re.escape(command)}(?:\(|\b)", lowered):
            # Negative warnings like "do not pass python files" are permitted.
            matching_lines = [ln.lower() for ln in text.splitlines() if _mentions_command(ln, command)]
            if any(not _is_negative_instruction(ln) for ln in matching_lines):
                issues.append(f"remaining_unavailable_command:{command}")
    if not contract.may_modify_testbench:
        if any(_requests_testbench_modification(ln.lower()) for ln in text.splitlines()):
            issues.append("remaining_testbench_modification_without_task_request")
    return sorted(set(issues))


def _is_bullet(line: str) -> bool:
    return re.match(r"^\s*(?:[-*]|\d+\.)\s+\S", line) is not None


def _strip_bullet(line: str) -> str:
    return re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line).strip()


def _normalize_directive(text: str) -> str:
    """Normalize a directive enough to spot repeated advice."""
    text = re.sub(r"`([^`]+)`", r"\1", text.lower())
    text = re.sub(r"[*_#>\[\]().,:;\"']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _directive_is_duplicate(text: str, seen: list[str]) -> bool:
    norm = _normalize_directive(text)
    if not norm:
        return True
    for prior in seen:
        if norm == prior:
            return True
        if len(norm) > 60 and len(prior) > 60 and SequenceMatcher(None, norm, prior).ratio() >= 0.9:
            return True
    seen.append(norm)
    return False


def _directive_is_vague(text: str) -> bool:
    lower = text.lower()
    vague_markers = (
        "consider ",
        "be mindful",
        "where possible",
        "as needed",
        "if appropriate",
        "try to ",
        "make sure to understand",
    )
    if any(marker in lower for marker in vague_markers):
        concrete_markers = (
            "ls",
            "cat",
            "echo",
            "edit",
            "iverilog",
            "vvp",
            "module",
            "port",
            "reset",
            "compile",
            "simulate",
            "testbench",
            "assert",
            "checker",
        )
        return not any(marker in lower for marker in concrete_markers)
    return False


def _line_importance_score(text: str, heading: str) -> int:
    lower = f"{heading} {text}".lower()
    score = 0
    for word in ("never", "must", "do not", "don't", "only", "exact", "critical", "hidden", "required"):
        if word in lower:
            score += 5
    for word in ("port", "width", "reset", "clock", "parameter", "path", "module", "interface", "protocol"):
        if word in lower:
            score += 4
    for word in ("edit", "echo", "cat", "ls", "iverilog", "vvp", "compile", "simulate", "write"):
        if word in lower:
            score += 3
    for word in ("fail", "error", "timeout", "debug", "probe", "assert", "checker", "mismatch"):
        if word in lower:
            score += 3
    if re.search(r"`[^`]+`|/[A-Za-z0-9_.\-/]+|\b[A-Za-z_][A-Za-z0-9_]*\.(?:v|sv|py|md)\b", text):
        score += 4
    if "hard-case" in lower or "prior" in lower or "pitfall" in lower:
        score += 2
    return score


def _directive_bucket(text: str, heading: str) -> str:
    lower = f"{heading} {text}".lower()
    if any(phrase in lower for phrase in ("never", "do not", "don't", "must not", "avoid", "forbid")):
        return "do_not"
    if any(phrase in lower for phrase in ("if compile", "compile fails", "simulation fail", "vvp", "timeout", "first error", "debug", "probe", "$display", "mismatch", "assertion")):
        return "failure_recovery"
    if any(phrase in lower for phrase in ("hard rule", "critical rule", "must ", "only ", "required")):
        return "hard_rules"
    if any(phrase in lower for phrase in ("hard-case", "prior", "pitfall", "cid", "module", "port", "width", "reset", "parameter", "protocol", "checker", "assertion", "exact path", "target file")):
        return "cid_guidance"
    return "procedure"


def _collect_skill_directives(text: str) -> tuple[str, dict[str, list[tuple[int, int, str]]], dict]:
    """Collect actionable directives from a skill without preserving verbosity."""
    title = "Skill"
    buckets: dict[str, list[tuple[int, int, str]]] = {
        "hard_rules": [],
        "cid_guidance": [],
        "procedure": [],
        "do_not": [],
        "failure_recovery": [],
    }
    metrics = {
        "input_directives": 0,
        "dropped_code_blocks": 0,
        "preserved_code_templates": 0,
        "dropped_vague_directives": 0,
        "dropped_duplicate_directives": 0,
    }
    seen: list[str] = []
    heading = ""
    in_code = False
    code_lines: list[str] = []
    order = 0
    paragraph_parts: list[str] = []

    def flush_paragraph() -> None:
        nonlocal order, paragraph_parts
        paragraph = " ".join(part.strip() for part in paragraph_parts if part.strip()).strip()
        paragraph_parts = []
        if not paragraph:
            return
        # Keep only short, directive-like paragraphs; prose introductions are
        # usually redundant after the canonical schema is reconstructed.
        if len(paragraph) > 260:
            return
        if not any(marker in paragraph.lower() for marker in (
            "must", "never", "do ", "use ", "read ", "write ", "compile", "simulate",
            "module", "port", "reset", "testbench", "checker", "assertion", "debug",
        )):
            return
        add_directive(paragraph)

    def add_directive(raw: str) -> None:
        nonlocal order
        item = raw.strip()
        if not item:
            return
        item = re.sub(r"\s+", " ", item)
        if _directive_is_vague(item):
            metrics["dropped_vague_directives"] += 1
            return
        if _directive_is_duplicate(item, seen):
            metrics["dropped_duplicate_directives"] += 1
            return
        bucket = _directive_bucket(item, heading)
        score = _line_importance_score(item, heading)
        buckets[bucket].append((score, order, item))
        metrics["input_directives"] += 1
        order += 1

    def flush_code_template() -> None:
        nonlocal code_lines
        code = "\n".join(code_lines).strip()
        code_lines = []
        if not code:
            return
        compact = re.sub(r"\s+", " ", code).strip()
        # Short protocol/RTL templates can carry the concrete lesson that made
        # a skill useful. Preserve only compact snippets; long code blocks are
        # still dropped because they dominate the injectable skill budget.
        template_heading = any(marker in heading.lower() for marker in ("template", "scaffold", "pattern", "example"))
        has_template_signal = re.search(
            r"\b(always|assign|assert|property|posedge|negedge|if|case|endcase)\b|\$fatal|\$display",
            compact,
        ) or (template_heading and re.search(r"\bmodule\b", compact))
        if len(compact) <= 520 and has_template_signal:
            metrics["preserved_code_templates"] += 1
            add_directive(f"Preserve this compact RTL/checker template when applicable: `{compact}`")
        else:
            metrics["dropped_code_blocks"] += 1

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            if in_code:
                flush_code_template()
                in_code = False
            else:
                code_lines = []
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            title = stripped
            heading = stripped.lstrip("#").strip()
            continue
        if re.match(r"^#{2,6}\s+\S", stripped):
            flush_paragraph()
            heading = re.sub(r"^#{2,6}\s+", "", stripped).strip()
            continue
        if _is_bullet(stripped):
            flush_paragraph()
            add_directive(_strip_bullet(stripped))
            continue
        if not stripped:
            flush_paragraph()
            continue
        paragraph_parts.append(stripped)
    if in_code:
        flush_code_template()
    flush_paragraph()
    return title, buckets, metrics


def _top_directives(items: list[tuple[int, int, str]], limit: int) -> list[str]:
    ranked = sorted(items, key=lambda item: (-item[0], item[1]))
    kept = sorted(ranked[:limit], key=lambda item: item[1])
    return [text for _, _, text in kept]


def _render_canonical_skill(
    title: str,
    buckets: dict[str, list[tuple[int, int, str]]],
    contract: SkillExecutionContract,
    limits: dict[str, int],
) -> str:
    """Render the compact, followable schema used for next-gen injection."""
    hard_rules = _hard_rules_section(contract).splitlines()[2:]
    hard_rule_texts = [line[2:].strip() for line in hard_rules if line.startswith("- ")]
    extra_hard = _top_directives(buckets["hard_rules"], max(0, limits["hard_rules"] - len(hard_rule_texts)))
    sections = [
        (title if title.startswith("# ") else f"# {title.lstrip('#').strip()}"),
        "",
        "## Hard Rules",
        "",
        *[f"- {item}" for item in [*hard_rule_texts, *extra_hard][:limits["hard_rules"]]],
        "",
        "## CID-Specific Guidance",
        "",
        *[f"- {item}" for item in _top_directives(buckets["cid_guidance"], limits["cid_guidance"])],
        "",
        "## Procedure",
        "",
        *[f"- {item}" for item in _top_directives(buckets["procedure"], limits["procedure"])],
        "",
        "## Do Not",
        "",
        *[f"- {item}" for item in _top_directives(buckets["do_not"], limits["do_not"])],
        "",
        "## Failure Recovery",
        "",
        *[f"- {item}" for item in _top_directives(buckets["failure_recovery"], limits["failure_recovery"])],
    ]
    # Remove empty sections that have no bullets after ranking, except hard
    # rules. Sparse sections add scanning overhead without guidance.
    rendered: list[str] = []
    i = 0
    while i < len(sections):
        line = sections[i]
        if line.startswith("## ") and line != "## Hard Rules":
            block = sections[i:i + 3]
            j = i + 3
            bullets = []
            while j < len(sections) and not sections[j].startswith("## "):
                if sections[j].startswith("- "):
                    bullets.append(sections[j])
                j += 1
            if not bullets:
                i = j
                continue
        rendered.append(line)
        i += 1
    return "\n".join(rendered).strip() + "\n"


def condense_skill(
    text: str,
    contract: SkillExecutionContract,
    sanitizer_cfg: dict | None = None,
    budget_chars: int = 0,
) -> tuple[str, dict]:
    """Condense an overly verbose skill into the canonical injectable schema.

    This is deliberately deterministic. It is not trying to invent new skill
    content; it keeps the highest-signal directives already present after
    sanitization, deduplicates them, and renders them in a small set of stable
    sections that are easier for a rollout model to follow.
    """
    cfg = sanitizer_cfg or {}
    condense_cfg = cfg.get("condense", {}) or {}
    if not condense_cfg.get("enabled", True):
        return text, {"enabled": False, "changed": False}

    raw_chars = len(text or "")
    over_chars = int(condense_cfg.get("over_chars", 6000))
    target_chars = int(condense_cfg.get("target_chars", 5200))
    if budget_chars > 0:
        target_chars = min(target_chars, budget_chars)
    soft_budget_slack_chars = int(condense_cfg.get("soft_budget_slack_chars", 1024))
    soft_budget_slack_ratio = float(condense_cfg.get("soft_budget_slack_ratio", 0.10))
    soft_budget_slack = 0
    if budget_chars > 0:
        soft_budget_slack = max(0, soft_budget_slack_chars, int(budget_chars * soft_budget_slack_ratio))

    # The length budget is a consolidation target, not a semantic guillotine.
    # A previous CID004 run showed that being only a few characters over budget
    # could trigger a full canonical rewrite and compact away useful procedure
    # details. Treat small budget overshoots as telemetry unless the skill is
    # also above the true verbosity threshold.
    within_hard_size = raw_chars <= over_chars
    within_soft_budget = not budget_chars or raw_chars <= budget_chars + soft_budget_slack
    if within_hard_size and within_soft_budget:
        return text, {
            "enabled": True,
            "changed": False,
            "pre_condense_chars": raw_chars,
            "post_condense_chars": raw_chars,
            "over_chars": over_chars,
            "target_chars": target_chars,
            "budget_chars": budget_chars,
            "soft_budget_slack": soft_budget_slack,
            "within_soft_budget": within_soft_budget,
            "hard_condense": False,
        }

    title, buckets, collect_metrics = _collect_skill_directives(text)
    limits = {
        "hard_rules": int(condense_cfg.get("max_hard_rules", 6)),
        "cid_guidance": int(condense_cfg.get("max_cid_guidance", 8)),
        "procedure": int(condense_cfg.get("max_procedure", 8)),
        "do_not": int(condense_cfg.get("max_do_not", 7)),
        "failure_recovery": int(condense_cfg.get("max_failure_recovery", 6)),
    }
    minimums = {
        "hard_rules": min(5, limits["hard_rules"]),
        "cid_guidance": min(3, limits["cid_guidance"]),
        "procedure": min(4, limits["procedure"]),
        "do_not": min(3, limits["do_not"]),
        "failure_recovery": min(3, limits["failure_recovery"]),
    }
    condensed = _render_canonical_skill(title, buckets, contract, limits)

    # If the compact schema is still too large, shrink softer sections first.
    shrink_order = ["procedure", "cid_guidance", "failure_recovery", "do_not", "hard_rules"]
    while len(condensed) > target_chars and any(limits[k] > minimums[k] for k in limits):
        for key in shrink_order:
            if limits[key] > minimums[key]:
                limits[key] -= 1
                break
        condensed = _render_canonical_skill(title, buckets, contract, limits)

    changed = condensed.strip() != (text or "").strip()
    min_retention_ratio = float(condense_cfg.get("min_retention_ratio", 0.75))
    min_retention_chars = int(raw_chars * min_retention_ratio)
    metrics = {
        "enabled": True,
        "changed": changed,
        "pre_condense_chars": raw_chars,
        "post_condense_chars": len(condensed),
        "delta_chars": len(condensed) - raw_chars,
        "over_chars": over_chars,
        "target_chars": target_chars,
        "budget_chars": budget_chars,
        "soft_budget_slack": soft_budget_slack,
        "within_soft_budget": within_soft_budget,
        "hard_condense": raw_chars > over_chars,
        "min_retention_ratio": min_retention_ratio,
        "min_retention_chars": min_retention_chars,
        "limits": limits,
        **collect_metrics,
    }
    if (
        changed
        and raw_chars <= over_chars
        and min_retention_ratio > 0
        and len(condensed) < min_retention_chars
    ):
        metrics.update(
            {
                "changed": False,
                "post_condense_chars": raw_chars,
                "delta_chars": 0,
                "rejected_low_retention": True,
                "rejected_condensed_chars": len(condensed),
            }
        )
        return text, metrics
    return condensed if changed else text, metrics


def sanitize_skill(
    candidate: str | None,
    parent_text: str,
    contract: SkillExecutionContract,
    max_chars: int = 0,
    sanitizer_cfg: dict | None = None,
) -> SanitizationResult:
    """Return a sanitized candidate skill and validation metadata."""
    cfg = sanitizer_cfg or {}
    if not cfg.get("enabled", True):
        text = (candidate or "").strip()
        return SanitizationResult(
            text=text,
            ok=bool(text),
            issues=[] if text else ["empty_output"],
            warnings=[],
            metrics={"candidate_chars": len(text), "parent_chars": len(parent_text), "enabled": False},
        )

    raw = (candidate or "").strip()
    issues: list[str] = []
    warnings: list[str] = []
    text, unfenced = _whole_document_unfence(raw)
    if unfenced:
        issues.append("removed_outer_markdown_fence")

    sanitized_lines: list[str] = []
    for line in text.splitlines():
        new_line = _replace_or_drop_impossible_line(line, contract, issues)
        if new_line is None:
            continue
        if new_line and (not sanitized_lines or sanitized_lines[-1] != new_line):
            sanitized_lines.append(new_line)
    text = "\n".join(sanitized_lines).strip() + "\n" if sanitized_lines else ""
    if text:
        text = _ensure_hard_rules(text, contract, issues)
    else:
        issues.append("empty_after_sanitization")

    budget = skill_length_budget(parent_text, max_chars, cfg)
    text, condense_metrics = condense_skill(
        text,
        contract,
        sanitizer_cfg=cfg,
        budget_chars=budget,
    )
    if condense_metrics.get("changed"):
        issues.append("condensed_verbose_skill")

    remaining = _scan_remaining_impossible(text, contract)
    issues.extend(remaining)
    warnings.extend(_low_actionability_warnings(text))

    excessive = bool(budget and len(text) > budget)
    if excessive:
        issues.append("excessive_length_growth")

    absolute_max = int(cfg.get("absolute_max_chars", 0) or 0)
    if absolute_max <= 0 and max_chars > 0:
        absolute_max = max_chars
    exceeds_absolute = bool(absolute_max and len(text) > absolute_max)
    if exceeds_absolute:
        issues.append("exceeds_absolute_max_chars")

    fatal = {
        "empty_after_sanitization",
        "exceeds_absolute_max_chars",
        "remaining_unavailable_edit_tool",
        "remaining_impossible_harness_run",
    }
    ok = bool(text) and not any(issue in fatal or issue.startswith("remaining_unavailable_command:") for issue in issues)
    metrics = {
        "parent_chars": len(parent_text or ""),
        "raw_candidate_chars": len(raw),
        "sanitized_chars": len(text),
        "delta_chars": len(text) - len(parent_text or ""),
        "budget_chars": budget,
        "absolute_max_chars": absolute_max,
        "allowed_tools": list(contract.allowed_tools),
        "visible_context_path_count": len(contract.visible_context_paths),
        "hidden_verifier": contract.hidden_verifier,
        "condense": condense_metrics,
    }
    return SanitizationResult(text=text.strip(), ok=ok, issues=sorted(set(issues)), warnings=warnings, metrics=metrics)


def write_sanitization_record(output_dir: Path, generation: int, record: dict) -> dict:
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generation": generation,
        **record,
    }
    for path in (output_dir / "skill_sanitization.jsonl", output_dir / f"gen{generation}" / "skill_sanitization.jsonl"):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


def candidate_skill_budget(parent_prompt: str, max_skill_length: int, sanitizer_cfg: dict) -> int:
    """Return the mutator-facing character budget for a child skill.

    The mutator receives the same budget that the deterministic sanitizer will
    later enforce. This encourages the LLM to consolidate the parent skill
    instead of growing an unbounded appendix of advice.
    """
    if not sanitizer_cfg.get("enabled", True):
        return max_skill_length
    return skill_length_budget(parent_prompt, max_skill_length, sanitizer_cfg)


def sanitize_candidate_skill(
    *,
    output_dir: Path,
    generation: int,
    child_slot: int,
    parent_info: str,
    stage: str,
    candidate: str,
    parent_prompt: str,
    max_skill_length: int,
    sanitizer_cfg: dict,
    execution_contract: SkillExecutionContract,
) -> tuple[str, dict]:
    """Sanitize a raw child skill and log the post-mutation decision.

    This is the handoff point between stochastic mutation/crossover and the
    deterministic optimizer loop. A returned skill is safe to inject into the
    next generation. A raised MutationValidationError means the optimizer should
    keep a parent/survivor instead of evaluating the child.
    """
    result = sanitize_skill(
        candidate=candidate,
        parent_text=parent_prompt,
        contract=execution_contract,
        max_chars=max_skill_length,
        sanitizer_cfg=sanitizer_cfg,
    )
    record = write_sanitization_record(
        output_dir,
        generation,
        {
            "stage": stage,
            "child_slot": child_slot,
            "parent_info": parent_info,
            **result.to_record(),
        },
    )
    if not result.ok:
        raise MutationValidationError(
            "skill sanitizer rejected candidate: " + ", ".join(result.issues)
        )
    return result.text, record


MUTATION_REFUSAL_PATTERNS = (
    "i can't",
    "i cannot",
    "i am unable",
    "as an ai",
    "sorry",
    "error code",
    "internalservererror",
    "traceback",
    "rate limit",
    "service unavailable",
)


def validate_mutated_skill(candidate: str | None, parent_prompt: str, max_chars: int = 0) -> dict:
    """Validate that post-processing produced an actual evolved skill.

    Sanitization answers "is this executable under the tool contract?" This
    second check answers "does this look like a real skill document rather than
    an empty/refusal/error response or an accidental parent echo?" Keeping both
    signals in one module makes mutation-health telemetry easier to interpret.
    """
    text = (candidate or "").strip()
    parent = (parent_prompt or "").strip()
    issues: list[str] = []

    parent_chars = len(parent)
    candidate_chars = len(text)
    metrics = {
        "parent_chars": parent_chars,
        "candidate_chars": candidate_chars,
        "delta_chars": candidate_chars - parent_chars,
        "max_chars": max_chars,
        "sha256": _sha256_text(text) if text else None,
        "parent_sha256": _sha256_text(parent) if parent else None,
    }

    if not text:
        issues.append("empty_output")
    if candidate_chars and candidate_chars < min(max(300, int(parent_chars * 0.2)), 1500):
        issues.append("too_short_for_skill")
    if max_chars > 0 and candidate_chars > int(max_chars * 1.05):
        issues.append("exceeds_character_budget")

    lower = text.lower()
    if any(pattern in lower for pattern in MUTATION_REFUSAL_PATTERNS):
        issues.append("looks_like_error_or_refusal")

    if text and parent:
        if text == parent:
            issues.append("unchanged_exact")
            metrics["similarity_to_parent"] = 1.0
        else:
            similarity = SequenceMatcher(None, parent[:12000], text[:12000]).ratio()
            metrics["similarity_to_parent"] = round(similarity, 6)
            if parent_chars >= 1000 and candidate_chars >= 1000 and similarity >= 0.995:
                issues.append("near_unchanged")

    heading_count = len(re.findall(r"(?m)^#{1,6}\s+\S", text))
    bullet_count = len(re.findall(r"(?m)^\s*(?:[-*]|\d+\.)\s+\S", text))
    metrics["heading_count"] = heading_count
    metrics["bullet_count"] = bullet_count
    if candidate_chars >= 300 and heading_count == 0 and bullet_count < 3:
        issues.append("not_skill_like_markdown")

    return {
        "ok": not issues,
        "issues": issues,
        "metrics": metrics,
    }


def write_mutation_health_record(output_dir: Path, generation: int, record: dict) -> dict:
    """Append mutation-health telemetry at run root and generation scope.

    These records intentionally avoid copying the full skill text. They give the
    monitor enough evidence to flag silent mutator failures while keeping the
    full skill artifacts in the normal per-generation skill files.
    """
    payload = _json_safe({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generation": generation,
        **record,
    })
    paths = [
        output_dir / "mutation_health.jsonl",
        output_dir / f"gen{generation}" / "mutation_health.jsonl",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


def risky_added_lines(previous_skill: str, current_skill: str, contract: SkillExecutionContract, limit: int = 12) -> list[str]:
    """Return newly added lines likely related to a regression."""
    risky: list[str] = []
    for line in unified_diff(previous_skill.splitlines(), current_skill.splitlines(), lineterm=""):
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:].strip()
        lower = body.lower()
        if not body or body.startswith("#"):
            continue
        if (
            ("harness" in lower and any(w in lower for w in ("run", "execute", "authoritative", "re-run")))
            or ("dependency" in lower)
            or ("vendor" in lower)
            or ("files.f" in lower)
            or ("traceability" in lower)
            or ("matrix" in lower)
            or ("edit" in lower and "edit" not in contract.allowed_tools)
        ):
            risky.append(body[:220])
        if len(risky) >= limit:
            break
    return risky


def _mode_counts_from_diagnostics(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rec in _load_jsonl(path):
        mode = str(rec.get("mode") or "unknown")
        counts[mode] = counts.get(mode, 0) + 1
    return dict(sorted(counts.items()))


def build_regression_reflection(
    *,
    output_dir: Path,
    gen_dir: Path,
    generation: int,
    previous_best_fitness: float,
    current_best_fitness: float,
    previous_skill: str,
    current_skill: str,
    execution_contract: SkillExecutionContract,
) -> str:
    """Write a regression-aware repair note for the next mutation.

    Regression reflection is part of post-mutation processing because it asks a
    narrow question about the just-injected child: "Which newly added skill
    lines may have caused the fitness drop?" The note then becomes evidence for
    the next mutator call, but the scanner and artifact contract stay here with
    the rest of the skill-quality gate.
    """
    drop = previous_best_fitness - current_best_fitness
    risky = risky_added_lines(previous_skill, current_skill, execution_contract)
    mode_counts = _mode_counts_from_diagnostics(gen_dir / "rollout_diagnostics.jsonl")
    lines = [
        f"# Regression reflection - Generation {generation}",
        "",
        f"Detected regression: previous generation best={previous_best_fitness:.3f}, "
        f"current generation best={current_best_fitness:.3f}, drop={drop:.3f}.",
        "",
        "## Failure-mode shift",
    ]
    if mode_counts:
        lines.extend(f"- {mode}: {count}" for mode, count in mode_counts.items())
    else:
        lines.append("- No rollout diagnostics found.")
    lines.extend([
        "",
        "## Newly added skill lines to scrutinize",
    ])
    if risky:
        lines.extend(f"- {line}" for line in risky)
    else:
        lines.append("- No obvious risky added lines were detected by the deterministic scanner.")
    lines.extend([
        "",
        "## Repair instruction for mutation",
        "- Do not continue blindly from the regressed child skill.",
        "- Prefer mutating from the best surviving parent or best-ever skill.",
        "- Remove or soften newly added guidance that is impossible under the rollout tool contract.",
        "- Convert hidden-harness advice into visible-file reading plus local simulator self-checks.",
        "- Keep only concise, executable rules that directly address observed failures.",
    ])
    text = "\n".join(lines).strip() + "\n"
    path = gen_dir / "regression_reflection.md"
    path.write_text(text, encoding="utf-8")
    _write_json(gen_dir / "regression_reflection.json", {
        "generation": generation,
        "previous_best_fitness": previous_best_fitness,
        "current_best_fitness": current_best_fitness,
        "drop": drop,
        "mode_counts": mode_counts,
        "risky_added_lines": risky,
        "path": _rel(path, output_dir),
    })
    return text
