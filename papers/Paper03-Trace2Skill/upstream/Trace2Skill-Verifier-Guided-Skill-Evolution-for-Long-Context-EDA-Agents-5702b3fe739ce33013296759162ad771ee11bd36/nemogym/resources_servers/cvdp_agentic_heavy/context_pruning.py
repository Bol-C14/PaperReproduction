"""Recoverable context pruning for CVDP agentic-heavy tasks.

This module implements an ablation path that is closer to how coding agents
usually handle large repositories: start with a compact file map and the most
likely useful files, then restore exact omitted files on demand.

The baseline converter remains unchanged. Use ``scripts/prune_cvdp_context.py``
to post-process an existing materialized JSONL into a pruned variant.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any


PRUNING_VERSION = "progressive_retrieval_v1"
CONTEXT_PRUNING_META_KEY = "context_pruning"
CONTEXT_MANIFEST_FILE = "CONTEXT_MANIFEST.md"
CONTEXT_PRUNING_REPORT_FILE = "CONTEXT_PRUNING_REPORT.md"


RESTORE_FILE_TOOL = {
    "type": "function",
    "name": "restore_file",
    "description": (
        "Restore an exact file that was omitted from the initial pruned context. "
        "Use this only for paths listed in CONTEXT_MANIFEST.md."
    ),
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "Sandbox-relative path of the pruned file to restore.",
            },
        },
        "required": ["filename"],
        "additionalProperties": False,
    },
}


EDIT_TOOL = {
    "type": "function",
    "name": "edit",
    "description": "Replace exactly one unique text span in an existing file.",
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "Path to the file to edit.",
            },
            "old_text": {
                "type": "string",
                "description": "Exact text to replace; must occur exactly once.",
            },
            "new_text": {
                "type": "string",
                "description": "Replacement text.",
            },
        },
        "required": ["filename", "old_text", "new_text"],
        "additionalProperties": False,
    },
}


PRUNING_DEVELOPER_HINT = """

CONTEXT PRUNING ABLATION:
The sandbox starts with a compact, high-signal subset of the repository rather
than every file. Read CONTEXT_MANIFEST.md if a path is missing or if you need
to understand what was omitted. If an omitted file is genuinely needed, call
restore_file(filename="path/from/manifest") to recover the exact original file,
then continue with cat/edit/echo/compile as usual.
"""


SOURCE_EXTS = {
    ".v",
    ".sv",
    ".vh",
    ".svh",
    ".py",
    ".tcl",
    ".xdc",
    ".sdc",
    ".qsf",
    ".qsys",
    ".xci",
    ".core",
    ".f",
    ".flist",
    ".mk",
    ".sh",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".scala",
    ".rs",
}

SMALL_TEXT_EXTS = {
    ".md",
    ".rst",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",
}

ALWAYS_DROP_EXTS = {
    ".gds",
    ".lef.gz",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".pdf",
    ".zip",
    ".tar",
    ".tgz",
    ".gz",
    ".xz",
    ".bz2",
    ".7z",
    ".vcd",
    ".fst",
    ".wdb",
    ".jou",
    ".rpt",
    ".log",
    ".out",
    ".o",
    ".so",
    ".a",
    ".class",
    ".jar",
}

DROP_DIR_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".cache",
    "build",
    "builds",
    "dist",
    "out",
    "output",
    "outputs",
    "obj_dir",
    "sim_build",
    "xsim.dir",
    "work",
    "logs",
    "reports",
    "waveforms",
}

SPECIAL_KEEP_NAMES = {
    "Makefile",
    "makefile",
    "CMakeLists.txt",
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
}

PATH_TOKEN_RE = re.compile(r"(?:/code/)?[A-Za-z0-9_./@+\-]+(?:\.[A-Za-z0-9_+\-]+)")
TB_RE = re.compile(r"(^|/)(tb|test|tests|verif|verification)(/|$)|(_tb|_test)\.(v|sv|py)$", re.IGNORECASE)


@dataclass
class PrunedFileInfo:
    path: str
    bytes: int
    reason: str
    sha256: str


@dataclass
class PruningResult:
    kept_files: dict[str, str]
    pruned_files: dict[str, str]
    pruned_manifest: list[PrunedFileInfo]
    referenced_paths: set[str]
    original_bytes: int
    kept_bytes: int

    @property
    def pruned_bytes(self) -> int:
        return self.original_bytes - self.kept_bytes

    @property
    def original_file_count(self) -> int:
        return len(self.kept_files) + len(self.pruned_files)


def _content_bytes(content: str) -> int:
    return len(content.encode("utf-8", errors="replace"))


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()


def _normal_path(path: str) -> str:
    path = path.strip()
    if path.startswith("/code/"):
        path = path[len("/code/") :]
    path = path.lstrip("/")
    return str(PurePosixPath(path))


def _path_parts(path: str) -> tuple[str, ...]:
    return tuple(part for part in PurePosixPath(path).parts if part not in ("", "."))


def _suffix(path: str) -> str:
    p = PurePosixPath(path)
    suffix = p.suffix.lower()
    # Treat .lef.gz and similar double extensions as compressed payloads.
    if suffix in {".gz", ".xz", ".bz2"} and len(p.suffixes) >= 2:
        return "".join(p.suffixes[-2:]).lower()
    return suffix


def _is_source_like(path: str) -> bool:
    return _suffix(path) in SOURCE_EXTS or PurePosixPath(path).name in SPECIAL_KEEP_NAMES


def _is_small_text(path: str) -> bool:
    return _suffix(path) in SMALL_TEXT_EXTS or PurePosixPath(path).name in SPECIAL_KEEP_NAMES


def _is_test_or_harness(path: str) -> bool:
    name = PurePosixPath(path).name
    return bool(TB_RE.search(path)) or name == "docker-compose.yml"


def _is_hidden_verifier_path(path: str) -> bool:
    """Hidden verifier implementation must not be visible or restorable.

    The real grading harness is carried separately in verifier_metadata and is
    mounted only during verify(). If repository materialization left harness
    directories or runner files in context_files, pruning should drop them from
    both the initial context and the restore manifest rather than advertising
    them to the rollout agent.
    """

    posix = PurePosixPath(path)
    parts = [part.lower() for part in posix.parts]
    return "harness" in parts or posix.name.lower() in {"harness.py", "test_runner.py"}


def _is_generated_or_build_path(path: str) -> bool:
    parts = {p.lower() for p in _path_parts(path)}
    return bool(parts & DROP_DIR_PARTS)


def extract_referenced_paths(prompt: str, context_files: dict[str, str], *metadata_maps: dict[str, Any] | None) -> set[str]:
    """Find context paths that the task appears to mention explicitly."""
    paths = {_normal_path(p) for p in context_files}
    by_basename: dict[str, list[str]] = {}
    for path in paths:
        by_basename.setdefault(PurePosixPath(path).name, []).append(path)

    haystacks = [prompt or ""]
    for metadata in metadata_maps:
        if metadata:
            haystacks.append(json.dumps(metadata, ensure_ascii=False))
    text = "\n".join(haystacks)

    referenced: set[str] = set()
    for path in paths:
        if path in text or f"/code/{path}" in text:
            referenced.add(path)

    for match in PATH_TOKEN_RE.findall(text):
        token = _normal_path(match)
        if token in paths:
            referenced.add(token)
            continue
        basename = PurePosixPath(token).name
        candidates = by_basename.get(basename, [])
        if len(candidates) == 1:
            referenced.add(candidates[0])

    return referenced


def _decision(
    path: str,
    content: str,
    referenced_paths: set[str],
    max_non_source_bytes: int,
    max_small_text_bytes: int,
) -> tuple[bool, str]:
    """Return (keep, reason). Explicit references and source-like files win."""
    if path in referenced_paths:
        return True, "explicitly referenced"

    name = PurePosixPath(path).name
    if name == "SKILL.md":
        return True, "skill file"

    if _is_test_or_harness(path):
        return True, "visible verification/config path"

    if _is_source_like(path):
        return True, "source-like file"

    size = _content_bytes(content)
    suffix = _suffix(path)

    if _is_generated_or_build_path(path):
        return False, "generated/build/cache path"

    if suffix in ALWAYS_DROP_EXTS:
        return False, f"low-signal extension {suffix}"

    if _is_small_text(path):
        if size <= max_small_text_bytes:
            return True, "small text/config/doc file"
        return False, f"large text/config/doc file over {max_small_text_bytes} bytes"

    if size > max_non_source_bytes:
        return False, f"large non-source file over {max_non_source_bytes} bytes"

    return True, "small uncategorized file"


def prune_context_files(
    context_files: dict[str, str],
    prompt: str,
    harness: dict[str, Any] | None = None,
    patch: dict[str, Any] | None = None,
    *,
    max_non_source_bytes: int = 256 * 1024,
    max_small_text_bytes: int = 128 * 1024,
) -> PruningResult:
    """Split context files into initial kept files and restorable pruned files."""
    normalized = {
        _normal_path(path): content
        for path, content in context_files.items()
        if not _is_hidden_verifier_path(_normal_path(path))
    }
    referenced = extract_referenced_paths(prompt, normalized, harness, patch)

    kept: dict[str, str] = {}
    pruned: dict[str, str] = {}
    manifest: list[PrunedFileInfo] = []
    original_bytes = 0
    kept_bytes = 0

    for path, content in sorted(normalized.items()):
        size = _content_bytes(content)
        original_bytes += size
        keep, reason = _decision(path, content, referenced, max_non_source_bytes, max_small_text_bytes)
        if keep:
            kept[path] = content
            kept_bytes += size
        else:
            pruned[path] = content
            manifest.append(PrunedFileInfo(path=path, bytes=size, reason=reason, sha256=_sha256(content)))

    return PruningResult(
        kept_files=kept,
        pruned_files=pruned,
        pruned_manifest=manifest,
        referenced_paths=referenced,
        original_bytes=original_bytes,
        kept_bytes=kept_bytes,
    )


def build_context_manifest(result: PruningResult, *, max_pruned_entries: int = 500) -> str:
    lines = [
        "# Context Manifest",
        "",
        "This task uses the progressive-retrieval context pruning ablation.",
        "Most source, visible testbench, script, and small config/doc files are present in /code.",
        "Large or low-signal files are omitted initially and can be recovered with restore_file(filename=...).",
        "",
        "## Summary",
        "",
        f"- Original files: {result.original_file_count}",
        f"- Initially available files: {len(result.kept_files)}",
        f"- Restorable pruned files: {len(result.pruned_files)}",
        f"- Original bytes: {result.original_bytes}",
        f"- Initially available bytes: {result.kept_bytes}",
        f"- Pruned bytes: {result.pruned_bytes}",
        "",
        "## Initially Available Files",
        "",
    ]
    for path in sorted(result.kept_files):
        lines.append(f"- {path} ({_content_bytes(result.kept_files[path])} bytes)")

    lines.extend(["", "## Restorable Pruned Files", ""])
    if result.pruned_manifest:
        for info in result.pruned_manifest[:max_pruned_entries]:
            lines.append(f"- {info.path} ({info.bytes} bytes): {info.reason}; sha256={info.sha256[:12]}")
        omitted = len(result.pruned_manifest) - max_pruned_entries
        if omitted > 0:
            lines.append(f"- ... {omitted} more pruned files omitted from this manifest view")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Restore Protocol",
            "",
            "If a missing file is needed for understanding, compilation, or verification, call:",
            "",
            'restore_file(filename="path/from/list/above")',
            "",
            "Then use cat(filename=...) or include the restored path in the compile command.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_pruning_report(result: PruningResult) -> str:
    pct = 0.0 if result.original_bytes == 0 else 100.0 * result.pruned_bytes / result.original_bytes
    top = sorted(result.pruned_manifest, key=lambda x: x.bytes, reverse=True)[:20]
    lines = [
        "# Context Pruning Report",
        "",
        f"- Version: {PRUNING_VERSION}",
        f"- Original files: {result.original_file_count}",
        f"- Initially available files: {len(result.kept_files)}",
        f"- Restorable pruned files: {len(result.pruned_files)}",
        f"- Original bytes: {result.original_bytes}",
        f"- Initially available bytes: {result.kept_bytes}",
        f"- Pruned bytes: {result.pruned_bytes} ({pct:.1f}%)",
        "",
        "## Explicitly Referenced Paths Kept",
        "",
    ]
    if result.referenced_paths:
        lines.extend(f"- {path}" for path in sorted(result.referenced_paths))
    else:
        lines.append("- None detected")

    lines.extend(["", "## Largest Pruned Files", ""])
    if top:
        for info in top:
            lines.append(f"- {info.path} ({info.bytes} bytes): {info.reason}")
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


def _task_prompt(row: dict[str, Any]) -> str:
    params = row.get("responses_create_params") or {}
    input_items = params.get("input") or []
    if isinstance(input_items, str):
        return input_items
    chunks: list[str] = []
    for item in input_items:
        if isinstance(item, dict) and item.get("role") == "user":
            chunks.append(str(item.get("content", "")))
    return "\n".join(chunks)


def _append_restore_tool(row: dict[str, Any]) -> None:
    params = row.setdefault("responses_create_params", {})
    tools = params.setdefault("tools", [])
    names = {tool.get("name") for tool in tools if isinstance(tool, dict)}
    if RESTORE_FILE_TOOL["name"] not in names:
        tools.append(copy.deepcopy(RESTORE_FILE_TOOL))


def _append_edit_tool(row: dict[str, Any]) -> None:
    params = row.setdefault("responses_create_params", {})
    tools = params.setdefault("tools", [])
    names = {tool.get("name") for tool in tools if isinstance(tool, dict)}
    if EDIT_TOOL["name"] not in names:
        insert_at = next(
            (idx + 1 for idx, tool in enumerate(tools) if isinstance(tool, dict) and tool.get("name") == "echo"),
            len(tools),
        )
        tools.insert(insert_at, copy.deepcopy(EDIT_TOOL))


def _append_developer_hint(row: dict[str, Any]) -> None:
    params = row.setdefault("responses_create_params", {})
    input_items = params.setdefault("input", [])
    if isinstance(input_items, str):
        params["input"] = [
            {"role": "developer", "content": PRUNING_DEVELOPER_HINT.strip()},
            {"role": "user", "content": input_items},
        ]
        return

    for item in input_items:
        if isinstance(item, dict) and item.get("role") == "developer":
            content = str(item.get("content", ""))
            if "CONTEXT PRUNING ABLATION" not in content:
                item["content"] = content.rstrip() + PRUNING_DEVELOPER_HINT
            return

    input_items.insert(0, {"role": "developer", "content": PRUNING_DEVELOPER_HINT.strip()})


def apply_pruning_to_row(
    row: dict[str, Any],
    *,
    store_path: str,
    max_non_source_bytes: int = 256 * 1024,
    max_small_text_bytes: int = 128 * 1024,
) -> tuple[dict[str, Any], dict[str, Any], PruningResult]:
    """Return (pruned_row, sidecar_store_payload, result)."""
    pruned_row = copy.deepcopy(row)
    meta = pruned_row.setdefault("verifier_metadata", {})
    context_files = meta.get("context_files") or {}
    if not isinstance(context_files, dict):
        raise ValueError("verifier_metadata.context_files must be a dict")

    prompt = _task_prompt(pruned_row)
    result = prune_context_files(
        context_files,
        prompt,
        harness=meta.get("harness_files") or {},
        patch=meta.get("patch") or {},
        max_non_source_bytes=max_non_source_bytes,
        max_small_text_bytes=max_small_text_bytes,
    )

    kept = dict(result.kept_files)
    kept[CONTEXT_MANIFEST_FILE] = build_context_manifest(result)
    kept[CONTEXT_PRUNING_REPORT_FILE] = build_pruning_report(result)
    meta["context_files"] = kept
    meta[CONTEXT_PRUNING_META_KEY] = {
        "enabled": True,
        "version": PRUNING_VERSION,
        "store_path": store_path,
        "original_file_count": result.original_file_count,
        "kept_file_count": len(result.kept_files),
        "pruned_file_count": len(result.pruned_files),
        "original_bytes": result.original_bytes,
        "kept_bytes": result.kept_bytes,
        "pruned_bytes": result.pruned_bytes,
        "pruned_manifest": [info.__dict__ for info in result.pruned_manifest],
    }

    _append_edit_tool(pruned_row)
    _append_restore_tool(pruned_row)
    _append_developer_hint(pruned_row)

    store_payload = {
        "version": PRUNING_VERSION,
        "task_id": meta.get("task_id"),
        "files": result.pruned_files,
    }
    return pruned_row, store_payload, result
