#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Converts CVDP agentic heavy compiled JSONL to NeMo-Gym format.
#
# Two-step process:
#   Step 1: Resolve context (clone repos at specified commits, inline file contents)
#   Step 2: Restructure into NeMo-Gym schema (responses_create_params + verifier_metadata)
#
# Usage:
#   python convert_to_gym.py \
#       --input  /path/to/20250801_agentic_heavy_compiled_all_categories.json \
#       --output resources_servers/cvdp_agentic_heavy/data/gym_cvdp_agentic_heavy.jsonl \
#       --repos-cache /tmp/cvdp_repos_cache
#
# CVDP v1.1.0 agentic-heavy rows reference sanitized local Git bundles by
# bare repo name. Set CVDP_HEAVY_REPOS_PATH or pass --heavy-repos-path to the
# directory containing cvdp_agentic_heavy_*.bundle files; the converter
# materializes the checked-out commit back into the NeMo-Gym context_files
# contract used by the rest of Trace2Skill.
#
# If --skip-resolve is passed, context references are kept as-is (for testing
# schema conversion only).

import argparse
import copy
import gzip
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional


AGENTIC_SYSTEM_PROMPT = """\
You are an expert hardware design engineer working in a sandbox at /code.

TOOLS — these are the ONLY tools. Any other call (bash, find, sed, grep, etc.) will FAIL:
  ls(path)              — list directory
  cat(filename)         — read file
  rg(pattern,path,glob) — search visible files for text/regex matches
  find_files(glob,path) — locate files by glob under a visible path
  read_file(filename,start_line,end_line)
                        — read a line range with line numbers
  show_changes(filename)— show diff from the original visible context
  module_index(path)    — summarize visible Verilog module declarations
  echo(content,filename)— write/overwrite a COMPLETE file
  edit(filename,old_text,new_text)
                        — replace one unique text span in an existing file
  restore_file(filename)— restore a listed file if context pruning is enabled
  iverilog(args)        — compile Verilog
  vvp(filename)         — run compiled simulation
  xcelium(args)         — run Cadence Xcelium/xrun when configured
  pwd()                 — print working directory

FINAL GRADING: After you finish, an external verifier checks the files in /code. Text answers are IGNORED. You MUST write files with echo or edit.

REQUIRED FLOW — follow these steps in order, using tool calls:

Step 1  cat(filename="SKILL.md")
        Read coding conventions and pitfalls. Do this first.

Step 2  ls(path=".")  then ls on each subdirectory you find.
        DO NOT guess paths. Use ls output to discover where files actually are.
        Common layouts: hardware/src/, src/, rtl/ — they vary per project.
        Use find_files/rg/module_index when the repo is large or a module,
        port, signal, or target path is unclear.

Step 3  cat the target file(s) mentioned in the task. If the task explicitly
        names a visible .v/.sv verification file, you may read it as a
        read-only interface/spec reference.
        Use read_file for large files once you know the relevant line range.

Step 4  Write your fix to the CORRECT path (the same path you read with cat).
        Prefer edit(filename,old_text,new_text) for surgical changes to existing files.
        Use echo(content,filename) for brand-new files or complete rewrites.
        After writing, use show_changes and/or cat/read_file to verify the
        change landed and did not touch unrelated files.

Step 5  iverilog(args="-o sim.vvp -g2012 <rtl_or_sv_files>")
        Compile your fix using only visible RTL/SystemVerilog files. If errors,
        fix and repeat from Step 4.
        DO NOT include Python, cocotb, pytest, or hidden verifier files in
        iverilog.
        Use -I<dir> if you get "Include file not found" errors.
        If visible files require full SystemVerilog features unsupported by
        iverilog and the xcelium tool is configured, use xcelium(args="...")
        as the compile/simulation tool instead.

Step 6  vvp(filename="sim.vvp")
        Run the simulation. NEVER skip this after a successful compile.
        Read the output: FAIL means fix and repeat from Step 4. PASS means done.
        If vvp hangs (timeout), your fix likely creates a combinational loop.

Repeat Steps 4-5-6 until tests pass. Each cycle is only 3 tool calls.

CRITICAL RULES:
- NEVER guess file paths. Always ls first to discover the actual directory structure.
- NEVER stop at compilation. Always run vvp after iverilog succeeds.
- NEVER give a text-only answer. You MUST use echo or edit to write files.
- NEVER spend more than 5 turns just reading. Start writing by turn 6-8.
- If stuck, re-read the task description — wrong assumptions compound silently."""


DENSE_VERIFIER_FEEDBACK_PROMPT = """\

OPTIONAL BLACK-BOX FUNCTIONAL FEEDBACK TOOL:
  verify_feedback(reason) — run the hidden verifier on a private copy of the current sandbox and return sanitized functional feedback plus safe waveform/VCD observations when available.

Use verify_feedback only when all of these are true:
- you already changed visible RTL/code with echo or edit;
- the current edited code has successfully compiled with iverilog;
- you have not already called verify_feedback for this exact code version;
- the remaining call budget is worth spending.

The hidden verifier remains invisible. Do not try to inspect harness internals, hidden files, hidden paths, docker-compose files, raw cocotb logs, raw VCD files, or reference solutions. Use only the sanitized functional feedback and safe observational waveform summary to guide the next visible RTL edit. Final grading still happens after the rollout."""


DENSE_VERIFIER_SKILL_ADDENDUM = """\

## Optional black-box functional feedback

If the `verify_feedback(reason)` tool is available, treat it as a scarce black-box check: call it only after a real visible code edit and a successful `iverilog` compile of that edited code. Use the sanitized functional result and safe waveform/VCD observations to choose the next RTL edit. Do not infer, request, or search for hidden harness files, raw verifier logs, raw waveform files, or reference solutions; final `/verify` remains the official reward.
"""


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "ls",
        "description": "List files and directories at the given path.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list. Defaults to current working directory."}
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "cat",
        "description": "Read and return the contents of a file.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Path to the file to read."}
            },
            "required": ["filename"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "rg",
        "description": "Search visible sandbox files for a text or regex pattern, similar to ripgrep.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for."},
                "path": {"type": "string", "description": "File or directory to search. Defaults to current directory."},
                "glob": {"type": "string", "description": "Optional filename glob such as '*.sv' or 'rtl/*'. Defaults to '*'."},
                "case_sensitive": {"type": "boolean", "description": "Whether matching is case-sensitive. Defaults to false."},
                "max_matches": {"type": "integer", "description": "Maximum matches to return. Defaults to 200."},
            },
            "required": ["pattern", "path", "glob", "case_sensitive", "max_matches"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "find_files",
        "description": "Find visible sandbox files by glob without reading their contents.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "glob": {"type": "string", "description": "Filename/path glob to match, such as '*.v' or '*/tb_*.sv'."},
                "path": {"type": "string", "description": "Directory to search. Defaults to current directory."},
                "max_results": {"type": "integer", "description": "Maximum results to return. Defaults to 300."},
            },
            "required": ["glob", "path", "max_results"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Read a specific line range from a visible sandbox file with line numbers.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Path to the file to read."},
                "start_line": {"type": "integer", "description": "1-based first line to read."},
                "end_line": {"type": "integer", "description": "1-based final line to read."},
            },
            "required": ["filename", "start_line", "end_line"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "show_changes",
        "description": "Show unified diffs between current files and the original visible context.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Optional single file to diff. Use empty string for all changes."},
                "max_files": {"type": "integer", "description": "Maximum changed files to show. Defaults to 40."},
            },
            "required": ["filename", "max_files"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "module_index",
        "description": "Summarize Verilog/SystemVerilog module declarations from visible files.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory to index. Defaults to current directory."}
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "echo",
        "description": "Write complete content to a file, creating or overwriting it.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to write to the file."},
                "filename": {"type": "string", "description": "Path to the file to write."},
            },
            "required": ["content", "filename"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "edit",
        "description": "Replace exactly one unique text span in an existing file.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Path to the file to edit."},
                "old_text": {"type": "string", "description": "Exact text to replace; must occur exactly once."},
                "new_text": {"type": "string", "description": "Replacement text."},
            },
            "required": ["filename", "old_text", "new_text"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "restore_file",
        "description": (
            "Restore an exact file omitted by recoverable context pruning. "
            "Use only for paths listed in CONTEXT_MANIFEST.md."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Sandbox-relative path of the pruned file to restore.",
                }
            },
            "required": ["filename"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "iverilog",
        "description": "Compile Verilog source files using Icarus Verilog.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "args": {"type": "string", "description": "Command-line arguments to pass to iverilog."}
            },
            "required": ["args"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "vvp",
        "description": "Run a compiled Verilog simulation.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Path to the compiled .out file to run."}
            },
            "required": ["filename"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "xcelium",
        "description": "Run Cadence Xcelium (xrun) commercial simulator. More powerful than iverilog — supports full SystemVerilog, UVM, coverage, and assertions.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "args": {"type": "string", "description": "Command-line arguments to pass to xrun."}
            },
            "required": ["args"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "pwd",
        "description": "Return the current working directory path.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
]


VERIFY_FEEDBACK_TOOL_DEFINITION = {
    "type": "function",
    "name": "verify_feedback",
    "description": (
        "Run the hidden verifier on a private copy of the current sandbox and return sanitized "
        "functional feedback plus safe waveform/VCD observations when available. Budgeted; "
        "allowed only after a visible edit and successful iverilog."
    ),
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Brief reason for requesting this scarce black-box feedback call.",
            }
        },
        "required": ["reason"],
        "additionalProperties": False,
    },
}


def tool_definitions(enable_verify_feedback_tool: bool = False) -> list[dict]:
    tools = copy.deepcopy(TOOL_DEFINITIONS)
    if enable_verify_feedback_tool and not any(tool.get("name") == "verify_feedback" for tool in tools):
        tools.append(copy.deepcopy(VERIFY_FEEDBACK_TOOL_DEFINITION))
    return tools


def agentic_system_prompt(enable_verify_feedback_tool: bool = False) -> str:
    if not enable_verify_feedback_tool:
        return AGENTIC_SYSTEM_PROMPT
    return AGENTIC_SYSTEM_PROMPT.rstrip() + "\n" + DENSE_VERIFIER_FEEDBACK_PROMPT


def skill_text_with_optional_verify_feedback(skill_text: Optional[str], enable_verify_feedback_tool: bool = False) -> Optional[str]:
    if not skill_text or not enable_verify_feedback_tool:
        return skill_text
    if "verify_feedback(reason)" in skill_text or "Optional black-box functional feedback" in skill_text:
        return skill_text
    return skill_text.rstrip() + "\n" + DENSE_VERIFIER_SKILL_ADDENDUM


def enable_runtime_verifier_feedback_in_gym_row(gym_row: dict) -> dict:
    """Mutate a NeMo-Gym row so dense verifier feedback is exposed to the agent.

    This function is intentionally opt-in. Sparse branches/materializations keep
    the original tool list and prompt, preserving the strict black-box contract.
    """
    params = gym_row.setdefault("responses_create_params", {})
    current_tools = params.get("tools")
    if isinstance(current_tools, list):
        params["tools"] = copy.deepcopy(current_tools)
        if not any(isinstance(tool, dict) and tool.get("name") == "verify_feedback" for tool in params["tools"]):
            params["tools"].append(copy.deepcopy(VERIFY_FEEDBACK_TOOL_DEFINITION))
    else:
        params["tools"] = tool_definitions(enable_verify_feedback_tool=True)
    inputs = params.setdefault("input", [])
    developer_seen = False
    for item in inputs:
        if isinstance(item, dict) and item.get("role") == "developer":
            developer_seen = True
            content = item.get("content", "")
            if "verify_feedback(reason)" not in content:
                item["content"] = str(content).rstrip() + "\n" + DENSE_VERIFIER_FEEDBACK_PROMPT
    if not developer_seen:
        inputs.insert(0, {"role": "developer", "content": agentic_system_prompt(True)})

    context_files = gym_row.setdefault("verifier_metadata", {}).setdefault("context_files", {})
    if "SKILL.md" in context_files:
        context_files["SKILL.md"] = skill_text_with_optional_verify_feedback(
            str(context_files["SKILL.md"]),
            enable_verify_feedback_tool=True,
        )
    return gym_row


VERILOG_EXT_SWAPS = {".sv": ".v", ".v": ".sv", ".svh": ".vh", ".vh": ".svh"}

HIDDEN_VERIFIER_FILENAMES = {
    "harness.py",
    "test_runner.py",
}

TRACE_SKILL_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SKILL_CANDIDATES = [
    TRACE_SKILL_ROOT / "skills" / "rollout" / "rtl_agent_skill.md",
    TRACE_SKILL_ROOT / "nemogym" / "data" / "rtl_agent_skill.md",
    Path(__file__).resolve().parent.parent / "data" / "SKILL.md",
]


def open_text_maybe_gzip(path: Path):
    """Open plain text or .gz task files with the same text interface."""
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open(encoding="utf-8", errors="replace")


def iter_json_rows(path: Path):
    """Yield rows from JSONL, JSONL.GZ, or a top-level JSON list/tasks file."""
    with open_text_maybe_gzip(path) as f:
        text = f.read()
    stripped = text.lstrip()
    if not stripped:
        return

    if stripped[0] in "[{":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if payload is not None:
            if isinstance(payload, dict) and "tasks" in payload:
                payload = payload["tasks"]
            if isinstance(payload, list):
                for row in payload:
                    yield row
                return
            if isinstance(payload, dict):
                yield payload
                return
            raise ValueError(f"Unexpected JSON top-level shape in {path}: {type(payload).__name__}")

    # Use literal newline splitting rather than splitlines(). JSON strings may
    # legally contain Unicode line separators such as U+2028; splitlines()
    # treats those as physical row boundaries and can corrupt otherwise valid
    # JSONL rows.
    for line_num, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_num}: invalid JSONL row: {exc}") from exc


def run_git(args: List[str], cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def is_remote_repo_reference(repo_url: str) -> bool:
    return "://" in repo_url or "@" in repo_url


def resolve_heavy_repo_reference(repo_ref: str, heavy_repos_path: Optional[str]) -> str:
    """Resolve v1.1.0 bare heavy repo names to local repos or .bundle files."""
    if not repo_ref or not heavy_repos_path:
        return repo_ref
    if os.path.isabs(repo_ref) or is_remote_repo_reference(repo_ref):
        return repo_ref

    base = Path(heavy_repos_path).expanduser()
    repo_path = base / repo_ref
    if repo_path.exists():
        return str(repo_path)
    bundle_path = base / f"{repo_ref}.bundle"
    if bundle_path.is_file():
        return str(bundle_path)
    return str(repo_path)


def _repo_cache_key(repo_url: str, commit: str) -> str:
    digest = hashlib.sha256(os.path.abspath(repo_url).encode("utf-8")).hexdigest()[:16]
    repo_name = Path(repo_url.removesuffix(".bundle")).name
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", repo_name).strip("._") or "repo"
    return f"{safe_name}_{digest}_{commit[:12]}"


def is_hidden_verifier_path(path: str) -> bool:
    """Return true for verifier/harness implementation files that must not be
    exposed to the rollout agent as part of the editable repository context.

    CVDP entries already carry the real grading payload under
    verifier_metadata.harness_files, which is mounted only during verify().
    Some cloned repos also contain benchmark harness directories or runner
    files. Keeping those in /code blurs the boundary between visible project
    files and hidden grading logic, and has caused prompts to tell the agent to
    compile pytest/cocotb files with iverilog. Filter them at materialization.
    """

    parts = PurePosixPath(path).parts
    lowered = [part.lower() for part in parts]
    if "harness" in lowered:
        return True
    return PurePosixPath(path).name.lower() in HIDDEN_VERIFIER_FILENAMES


def resolve_skill_file(path_arg: Optional[str]) -> Optional[Path]:
    """Resolve the SKILL.md file injected into every task context."""
    if path_arg:
        path = Path(path_arg)
        if not path.exists():
            raise FileNotFoundError(f"skill file not found: {path}")
        return path

    for candidate in DEFAULT_SKILL_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def ensure_repo_checkout(repo_url: str, commit: str, cache_dir: str) -> str:
    """Ensure cache_dir contains a usable worktree for repo_url at commit."""
    repo_dir = os.path.join(cache_dir, _repo_cache_key(repo_url, commit))

    if not os.path.exists(repo_dir):
        print(f"  Cloning {repo_url} @ {commit[:12]}...")
        run_git(["clone", "--no-checkout", repo_url, repo_dir])
    else:
        print(f"  Using cached {repo_dir}")
        if not os.path.isdir(os.path.join(repo_dir, ".git")):
            raise RuntimeError(f"cached path is not a git repo: {repo_dir}")

    have_commit = run_git(["rev-parse", "--verify", f"{commit}^{{commit}}"], cwd=repo_dir, check=False)
    if have_commit.returncode != 0:
        print(f"  Fetching missing commit {commit[:12]}...")
        fetch_one = run_git(["fetch", "origin", commit], cwd=repo_dir, check=False)
        if fetch_one.returncode != 0:
            run_git(["fetch", "origin", "+refs/heads/*:refs/remotes/origin/*"], cwd=repo_dir)

    # Cached worktrees may exist but have all tracked files deleted from a
    # previous interrupted materialization. Force checkout is safe here because
    # this directory is a generated cache, not user-authored source.
    run_git(["checkout", "-f", commit], cwd=repo_dir)
    return repo_dir


def clone_and_read_files(repo_url: str, commit: str, cache_dir: str) -> Dict[str, str]:
    """Clone a repo at a specific commit and read all text files into a dict."""
    repo_dir = ensure_repo_checkout(repo_url, commit, cache_dir)

    # Remap external/* -> root: harness expects /code/src/... not /code/external/src/...
    has_external = os.path.isdir(os.path.join(repo_dir, "external"))

    files: Dict[str, str] = {}
    for root, dirs, filenames in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if d != ".git"]
        for fname in filenames:
            fpath = os.path.join(root, fname)
            relpath = os.path.relpath(fpath, repo_dir)
            if has_external and relpath.startswith("external/"):
                relpath = relpath[len("external/"):]
            if is_hidden_verifier_path(relpath):
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    files[relpath] = f.read()
            except (IOError, UnicodeDecodeError):
                continue

    return files


def normalize_harness_files(harness: dict) -> Dict[str, Optional[str]]:
    """Return the hidden verifier file map from old or v1.1.0 dataset rows."""
    if not isinstance(harness, dict):
        return {}
    files = harness.get("files")
    if isinstance(files, dict):
        return files
    return harness


def fix_prompt_paths(prompt: str, context_files: Dict[str, str], task_id: str) -> str:
    """Fix file path references in the user prompt to match actual context_files.

    Handles:
    - /code/ prefix (strip to get sandbox-relative)
    - .sv <-> .v extension swaps
    - external/ prefix (already stripped from context_files by clone_and_read_files)
    """
    context_set = set(context_files.keys())
    by_basename: Dict[str, List[str]] = {}
    for path in context_set:
        if is_hidden_verifier_path(path):
            continue
        by_basename.setdefault(os.path.basename(path), []).append(path)

    def _fix_one(match: re.Match) -> str:
        full = match.group(0)
        rel = full.replace("/code/", "", 1)

        if rel in context_set:
            return full

        stem, ext = os.path.splitext(rel)
        swapped_ext = VERILOG_EXT_SWAPS.get(ext)
        if swapped_ext:
            candidate = stem + swapped_ext
            if candidate in context_set:
                fixed = "/code/" + candidate
                print(f"  [{task_id}] path fix: {full} -> {fixed}")
                return fixed

        for prefix in ["external/", "src/", "rtl/"]:
            candidate = prefix + rel
            if candidate in context_set:
                fixed = "/code/" + candidate
                print(f"  [{task_id}] path fix: {full} -> {fixed}")
                return fixed
            if swapped_ext:
                candidate2 = prefix + stem + swapped_ext
                if candidate2 in context_set:
                    fixed = "/code/" + candidate2
                    print(f"  [{task_id}] path fix: {full} -> {fixed}")
                    return fixed

        basename_matches = by_basename.get(os.path.basename(rel), [])
        if len(basename_matches) == 1:
            fixed = "/code/" + basename_matches[0]
            print(f"  [{task_id}] basename path fix: {full} -> {fixed}")
            return fixed

        return full

    return re.sub(r"/code/[\w/.+\-]+\.\w+", _fix_one, prompt)


VISIBLE_VERILOG_TB_PATTERNS = re.compile(
    r"(^|/)("
    r"tb_\w+\.(v|sv|vh|svh)"
    r"|\w+_tb\.(v|sv|vh|svh)"
    r"|test_\w+\.(v|sv|vh|svh)"
    r"|\w+_test\.(v|sv|vh|svh)"
    r")$",
    re.IGNORECASE,
)


def find_visible_verilog_testbenches(context_files: Dict[str, str]) -> List[str]:
    """Find visible Verilog/SystemVerilog verification files.

    Python/cocotb tests and hidden harness paths are deliberately excluded.
    The rollout may read a visible .v/.sv testbench when the task calls for it,
    but the converter must never advertise hidden verifier files as something
    the agent should compile or run.
    """

    return sorted(
        p for p in context_files
        if not is_hidden_verifier_path(p) and VISIBLE_VERILOG_TB_PATTERNS.search(p)
    )


def enrich_prompt_with_testbenches(prompt: str, testbenches: List[str], task_id: str) -> str:
    """Optionally prepend a conservative visible-verification-file index.

    This is disabled by default. When explicitly enabled for an ablation, it
    lists only visible .v/.sv-style files and avoids giving a runnable command,
    because a generic iverilog recipe is often wrong for multi-file projects.
    """
    if not testbenches:
        return prompt

    shown = testbenches[:8]
    tb_list = "\n".join(f"  - {tb}" for tb in shown)
    extra = f" (and {len(testbenches) - 8} more)" if len(testbenches) > 8 else ""

    hint = (
        f"VISIBLE VERILOG/SYSTEMVERILOG VERIFICATION FILES{extra}:\n{tb_list}\n\n"
        f"These files are visible project artifacts. Read them only when they are "
        f"relevant to the task, and compile only .v/.sv/.vh/.svh files.\n\n"
        f"---\n\n"
    )

    print(f"  [{task_id}] found {len(testbenches)} visible Verilog/SV verification files, prepended opt-in hint")
    return hint + prompt


HIDDEN_HARNESS_PROMPT_PATH_RE = re.compile(
    r"`?/code/(?:[\w.+\-]+/)*harness/[\w./+\-]+`?",
    re.IGNORECASE,
)
RUN_COCOTB_TESTBENCH_BULLET_RE = re.compile(
    r"(?m)^\s*\*\s+Run the existing cocotb testbench\b.*$",
    re.IGNORECASE,
)


def sanitize_prompt_for_agent_tools(prompt: str, task_id: str) -> str:
    """Remove hidden-verifier paths and impossible testbench instructions.

    The v1.1.0 public tasks sometimes describe failure modes observed by a
    cocotb harness. The behavioral facts are useful and should remain, but the
    rollout agent must not see hidden harness paths or be told to run tools that
    are not exposed to it. Final correctness is still checked by verify().
    """

    original = prompt
    prompt = re.sub(
        r"\s*\(located at\s+`?/code/(?:[\w.+\-]+/)*harness/[\w./+\-]+`?\)",
        " (used by the external verifier)",
        prompt,
        flags=re.IGNORECASE,
    )
    prompt = HIDDEN_HARNESS_PROMPT_PATH_RE.sub("the hidden external verifier", prompt)
    prompt = RUN_COCOTB_TESTBENCH_BULLET_RE.sub(
        "* Use the behavioral requirements above and visible RTL checks when possible; "
        "the external verifier will run the hidden cocotb tests against your final RTL.",
        prompt,
    )
    if prompt != original:
        print(f"  [{task_id}] sanitized hidden verifier/tool references in prompt")
    return prompt


def convert_entry(
    entry: dict,
    cache_dir: Optional[str],
    skip_resolve: bool,
    skill_text: Optional[str],
    *,
    include_testbench_hints: bool = False,
    enable_verify_feedback_tool: bool = False,
    heavy_repos_path: Optional[str] = None,
    source_path: Optional[Path] = None,
) -> Optional[dict]:
    """Convert one CVDP agentic heavy entry to NeMo-Gym format."""
    task_id = entry.get("id", "")
    categories = entry.get("categories", [])
    difficulty = categories[1] if len(categories) > 1 else ""
    prompt = entry.get("prompt", "")
    context = entry.get("context", {})
    origin = entry.get("origin", {})
    patch = entry.get("patch", {})
    harness = normalize_harness_files(entry.get("harness", {}))
    source_context = dict(context) if isinstance(context, dict) else {}

    # Step 1: Resolve context
    if skip_resolve:
        context_files = {"_unresolved": json.dumps(context)}
    else:
        repo_url = context.get("repo", "")
        commit = context.get("commit", "")
        if not repo_url or not commit:
            print(f"  Skipping {task_id}: missing repo or commit in context")
            return None
        resolved_repo_url = resolve_heavy_repo_reference(repo_url, heavy_repos_path)
        if resolved_repo_url != repo_url:
            print(f"  Resolved {repo_url} -> {resolved_repo_url}")
        try:
            context_files = clone_and_read_files(resolved_repo_url, commit, cache_dir)
        except Exception as e:
            print(f"  Skipping {task_id}: failed to clone — {e}")
            return None
        source_context["resolved_repo"] = resolved_repo_url

    # Step 2: Inject SKILL.md into context_files
    if skill_text:
        skill_text = skill_text_with_optional_verify_feedback(
            skill_text,
            enable_verify_feedback_tool=enable_verify_feedback_tool,
        )
        context_files["SKILL.md"] = skill_text

    # Step 3: Fix file path references in the user prompt
    if not skip_resolve:
        prompt = fix_prompt_paths(prompt, context_files, task_id)
    prompt = sanitize_prompt_for_agent_tools(prompt, task_id)

    # Step 4: Optional visible verification-file index.
    # Disabled by default so hidden harness/test runner details stay invisible.
    if include_testbench_hints and not skip_resolve:
        testbenches = find_visible_verilog_testbenches(context_files)
        prompt = enrich_prompt_with_testbenches(prompt, testbenches, task_id)

    # Step 5: Build NeMo-Gym structure
    gym_row = {
        "responses_create_params": {
            "input": [
                {"role": "developer", "content": agentic_system_prompt(enable_verify_feedback_tool)},
                {"role": "user", "content": prompt},
            ],
            "tools": tool_definitions(enable_verify_feedback_tool),
        },
        "verifier_metadata": {
            "task_id": task_id,
            "categories": categories,
            "difficulty": difficulty,
            "context_files": context_files,
            "harness_files": harness,
            "patch": patch,
            "origin": origin,
            "source_context": source_context,
            "source_file": str(source_path) if source_path else None,
        },
    }
    return gym_row


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert CVDP agentic heavy data to NeMo-Gym format")
    parser.add_argument("--input", required=True, help="Input JSONL or JSONL.GZ (agentic heavy compiled/v1.1.0)")
    parser.add_argument("--output", required=True, help="Output NeMo-Gym JSONL")
    parser.add_argument("--repos-cache", default="/tmp/cvdp_repos_cache",
                        help="Directory to cache cloned repos")
    parser.add_argument("--heavy-repos-path", default=os.environ.get("CVDP_HEAVY_REPOS_PATH"),
                        help="Directory containing v1.1.0 cvdp_agentic_heavy_* repos or .bundle files")
    parser.add_argument("--skip-resolve", action="store_true",
                        help="Skip resolving context URLs (for testing schema conversion only)")
    parser.add_argument("--skill-file", default=None,
                        help="SKILL.md to inject into every task context (default: Trace2Skill rollout skill)")
    parser.add_argument("--no-skill", action="store_true",
                        help="Do not inject SKILL.md into task contexts")
    parser.add_argument("--include-testbench-hints", action="store_true",
                        help="Opt in to a conservative visible .v/.sv verification-file index. Disabled by default.")
    parser.add_argument("--enable-verify-feedback-tool", action="store_true",
                        help="Expose the opt-in runtime verify_feedback(reason) tool and prompt guidance.")
    parser.add_argument("--allow-with-solutions", action="store_true",
                        help="Allow *_with_solutions source files. Keep unset for rollout datasets.")
    args = parser.parse_args()

    input_path = Path(args.input)
    if "with_solutions" in input_path.name and not args.allow_with_solutions:
        raise SystemExit(
            "Refusing to convert a *_with_solutions dataset for rollout use. "
            "Pass --allow-with-solutions only for explicit oracle/debug workflows."
        )

    os.makedirs(args.repos_cache, exist_ok=True)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    skill_text = None
    if not args.no_skill:
        skill_file = resolve_skill_file(args.skill_file)
        if skill_file:
            skill_text = skill_file.read_text()
            print(f"[skill] Injecting {skill_file}")
        else:
            print("[skill] WARNING: no SKILL.md found to inject")

    written = 0
    skipped = 0
    with open(args.output, "w") as fout:
        for line_num, entry in enumerate(iter_json_rows(input_path), 1):
            task_id = entry.get("id", f"line_{line_num}")
            print(f"[{line_num}] Processing {task_id}...")

            gym_row = convert_entry(
                entry,
                args.repos_cache,
                args.skip_resolve,
                skill_text,
                include_testbench_hints=args.include_testbench_hints,
                enable_verify_feedback_tool=args.enable_verify_feedback_tool,
                heavy_repos_path=args.heavy_repos_path,
                source_path=input_path,
            )
            if gym_row is None:
                skipped += 1
                continue

            fout.write(json.dumps(gym_row) + "\n")
            written += 1

    print(f"\nDone. Wrote {written} entries to {args.output}")
    if skipped:
        print(f"Skipped {skipped} entries (no repo access or missing context)")


if __name__ == "__main__":
    main()
