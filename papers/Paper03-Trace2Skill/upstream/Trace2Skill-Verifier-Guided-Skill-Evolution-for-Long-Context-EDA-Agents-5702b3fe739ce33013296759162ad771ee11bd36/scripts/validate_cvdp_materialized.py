#!/usr/bin/env python3
"""Validate materialized CVDP agentic-heavy NeMo-Gym JSONL splits.

This is a data-readiness check, not a rollout run. It verifies that generated
train/test JSONLs can be parsed and satisfy the CVDP resource server's expected
shape before we spend hours on rollouts.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


CID_LABELS = {
    "cid003": "spec_to_rtl",
    "cid004": "rtl_refine_design",
    "cid005": "code_completion",
    "cid012": "stimulus_tb_generation",
    "cid013": "testbench_checker_extension",
    "cid014": "sva_assertions",
    "cid016": "verification_bug_fix",
}

REQUIRED_TOOLS = {
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
}
SUPPORTED_TOOLS = REQUIRED_TOOLS | {"restore_file", "xcelium", "verify_feedback"}
SOURCE_EXTS = {".v", ".sv", ".vh", ".svh", ".tcl", ".py", ".md", ".txt", ".json", ".yml", ".yaml"}
RTL_EXTS = {".v", ".sv", ".vh", ".svh"}
CODE_PATH_RE = re.compile(r"(?:/code/|code/)([\w./+\-]+\.\w+)")
PYTHON_IVERILOG_RE = re.compile(r"iverilog\s*\([^\)]*\.py\b", re.IGNORECASE | re.DOTALL)
HIDDEN_PROMPT_PATH_RE = re.compile(
    r"(^|[\s\"'`(])(?:/code/|code/)?(?:[\w./+\-]*/)?harness/|(?:test_runner|harness)\.py\b",
    re.IGNORECASE,
)
GENERATED_TESTBENCH_HINT_MARKERS = (
    "AVAILABLE TESTBENCHES in this project",
    "Use these to verify your fix. After writing your changes",
)


def _open_text_maybe_gzip(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open(encoding="utf-8", errors="replace")


def _iter_source_rows(path: Path):
    with _open_text_maybe_gzip(path) as f:
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
    # Do not use splitlines(): valid JSON strings can contain Unicode line
    # separators that Python would treat as row breaks.
    for line_num, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_num}: source JSON invalid: {exc}") from exc


class Validator:
    def __init__(self, data_root: Path, source: Path | None, manifest: Path | None) -> None:
        self.data_root = data_root
        self.source = source
        self.manifest = manifest
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.rows: list[tuple[Path, int, dict[str, Any]]] = []
        self.counts_by_split: Counter[str] = Counter()
        self.counts_by_cid: Counter[str] = Counter()
        self.task_locations: defaultdict[str, list[str]] = defaultdict(list)
        self._manifest_payload: dict[str, Any] | None = None

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")

    def validate(self) -> int:
        self._load_rows()
        self._validate_rows()
        self._validate_manifest()
        self._validate_source_coverage()
        self._print_report()
        return 1 if self.errors else 0

    def _load_rows(self) -> None:
        paths = sorted(self.data_root.glob("cid*_*/*.jsonl"))
        if not paths:
            self.error(str(self.data_root), "no per-CID JSONL files found")
            return

        for path in paths:
            split_name = f"{path.parent.name}/{path.name}"
            with path.open(encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        self.error(f"{path}:{line_num}", f"invalid JSON: {exc}")
                        continue
                    self.rows.append((path, line_num, row))
                    self.counts_by_split[split_name] += 1

    def _validate_rows(self) -> None:
        seen_in_split: defaultdict[str, set[str]] = defaultdict(set)

        for path, line_num, row in self.rows:
            where = f"{path}:{line_num}"
            split_name = f"{path.parent.name}/{path.name}"

            params = row.get("responses_create_params")
            if not isinstance(params, dict):
                self.error(where, "missing responses_create_params object")
                continue

            self._validate_input(where, params.get("input"))
            self._validate_prompt_hygiene(where, params.get("input"))
            self._validate_tools(where, params.get("tools"))

            meta = row.get("verifier_metadata")
            if not isinstance(meta, dict):
                self.error(where, "missing verifier_metadata object")
                continue

            task_id = meta.get("task_id")
            if not isinstance(task_id, str) or not task_id:
                self.error(where, "verifier_metadata.task_id must be a non-empty string")
                task_id = f"unknown:{where}"
            elif not task_id.startswith("cvdp_agentic_heavy_"):
                self.warn(where, f"unexpected task_id prefix: {task_id}")

            if task_id in seen_in_split[split_name]:
                self.error(where, f"duplicate task_id inside split: {task_id}")
            seen_in_split[split_name].add(task_id)
            self.task_locations[task_id].append(split_name)

            categories = meta.get("categories")
            if not isinstance(categories, list) or len(categories) < 2:
                self.error(where, "categories must contain CID and difficulty")
                cid = "unknown"
            else:
                cid = next((c for c in categories if isinstance(c, str) and c.startswith("cid")), None)
                if cid is None:
                    self.error(where, f"no CID category in {categories}")
                    cid = "unknown"
                elif cid not in CID_LABELS:
                    self.warn(where, f"CID not in known Trace2Skill taxonomy: {cid}")
                difficulty = meta.get("difficulty")
                if difficulty != categories[1]:
                    self.warn(where, f"difficulty {difficulty!r} does not match categories[1] {categories[1]!r}")
            self.counts_by_cid[cid] += 1

            if not path.parent.name.startswith(f"{cid}_") and cid != "unknown":
                self.error(where, f"path folder {path.parent.name!r} does not match CID {cid}")
            expected_label = CID_LABELS.get(cid)
            if expected_label and path.parent.name != f"{cid}_{expected_label}":
                self.error(where, f"folder label should be {cid}_{expected_label}")

            context_files = meta.get("context_files")
            harness_files = meta.get("harness_files")
            self._validate_file_map(where, "context_files", context_files, allow_none=False)
            self._validate_file_map(where, "harness_files", harness_files, allow_none=True)

            if isinstance(context_files, dict):
                self._validate_context(where, context_files)
                self._validate_prompt_paths(where, params.get("input"), context_files, harness_files)
            if isinstance(harness_files, dict):
                self._validate_harness(where, harness_files)

            patch = meta.get("patch")
            if patch is not None and not isinstance(patch, dict):
                self.error(where, "patch must be an object or null")
            origin = meta.get("origin")
            if origin is not None and not isinstance(origin, dict):
                self.error(where, "origin must be an object or null")

        for task_id, locations in sorted(self.task_locations.items()):
            if len(locations) > 1:
                self.error(task_id, f"appears in multiple splits: {locations}")

    def _validate_input(self, where: str, value: Any) -> None:
        if not isinstance(value, list) or len(value) < 2:
            self.error(where, "responses_create_params.input must contain developer and user messages")
            return
        roles = [item.get("role") for item in value if isinstance(item, dict)]
        if roles[:2] != ["developer", "user"]:
            self.error(where, f"first two input roles should be developer,user; got {roles[:2]}")
        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                self.error(where, f"input[{idx}] is not an object")
                continue
            content = item.get("content")
            if not isinstance(content, str) or not content.strip():
                self.error(where, f"input[{idx}].content must be non-empty text")

    def _validate_tools(self, where: str, value: Any) -> None:
        if not isinstance(value, list):
            self.error(where, "responses_create_params.tools must be a list")
            return
        names: list[str] = []
        for idx, tool in enumerate(value):
            if not isinstance(tool, dict):
                self.error(where, f"tools[{idx}] is not an object")
                continue
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                self.error(where, f"tools[{idx}].name must be non-empty")
                continue
            names.append(name)
            if name not in SUPPORTED_TOOLS:
                self.error(where, f"tool {name!r} is not supported by cvdp_agentic_heavy app.py")
            if tool.get("type") != "function":
                self.error(where, f"tool {name}: type must be function")
            if tool.get("strict") is not True:
                self.error(where, f"tool {name}: strict must be true")
            params = tool.get("parameters")
            if not isinstance(params, dict) or params.get("type") != "object":
                self.error(where, f"tool {name}: parameters must be an object schema")
        missing = REQUIRED_TOOLS - set(names)
        if missing:
            self.error(where, f"missing required tools: {sorted(missing)}")
        duplicates = [name for name, count in Counter(names).items() if count > 1]
        if duplicates:
            self.error(where, f"duplicate tool definitions: {duplicates}")

    def _validate_file_map(self, where: str, label: str, value: Any, allow_none: bool) -> None:
        if not isinstance(value, dict) or not value:
            self.error(where, f"{label} must be a non-empty object")
            return
        for relpath, content in value.items():
            if not isinstance(relpath, str) or not relpath:
                self.error(where, f"{label} contains an invalid path key")
                continue
            if not self._safe_relpath(relpath):
                self.error(where, f"{label} path escapes sandbox or is absolute: {relpath!r}")
            if content is None and allow_none:
                continue
            if not isinstance(content, str):
                self.error(where, f"{label}[{relpath!r}] must be text")

    def _validate_context(self, where: str, context_files: dict[str, str]) -> None:
        if "_unresolved" in context_files:
            self.error(where, "context_files still contains _unresolved; repo contents were not materialized")
        hidden_paths = [p for p in context_files if self._hidden_verifier_context_path(p)]
        if hidden_paths:
            shown = sorted(hidden_paths)[:5]
            suffix = "" if len(hidden_paths) <= 5 else f" (+{len(hidden_paths) - 5} more)"
            self.error(where, f"context_files exposes hidden verifier/harness paths: {shown}{suffix}")
        skill = context_files.get("SKILL.md")
        if not isinstance(skill, str) or len(skill.strip()) < 100:
            self.error(where, "SKILL.md is missing or too small")
        rtl_files = [p for p in context_files if PurePosixPath(p).suffix in RTL_EXTS]
        if not rtl_files:
            self.warn(where, "no RTL/SystemVerilog files detected in context_files")
        textish = [p for p in context_files if PurePosixPath(p).suffix in SOURCE_EXTS]
        if len(textish) < 2:
            self.warn(where, "very few source-like files detected in context_files")

    @staticmethod
    def _hidden_verifier_context_path(path: str) -> bool:
        posix = PurePosixPath(path)
        parts = [part.lower() for part in posix.parts]
        return "harness" in parts or posix.name.lower() in {"harness.py", "test_runner.py"}

    def _validate_prompt_hygiene(self, where: str, input_items: Any) -> None:
        if not isinstance(input_items, list):
            return
        contents: list[tuple[str, str]] = []
        for item in input_items:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", ""))
            content = item.get("content")
            if isinstance(content, str):
                contents.append((role, content))
        if not contents:
            return

        joined = "\n".join(content for _, content in contents)
        for marker in GENERATED_TESTBENCH_HINT_MARKERS:
            if marker in joined:
                self.error(where, f"prompt contains deprecated generated testbench hint marker: {marker!r}")
        if PYTHON_IVERILOG_RE.search(joined):
            self.error(where, "prompt tells the agent to pass a Python/cocotb/pytest file to iverilog")
        if HIDDEN_PROMPT_PATH_RE.search(joined):
            self.error(where, "prompt exposes hidden verifier/harness path or test_runner.py")

    def _validate_harness(self, where: str, harness_files: dict[str, Any]) -> None:
        compose_keys = [p for p in harness_files if p.endswith("docker-compose.yml")]
        if not compose_keys:
            self.error(where, "harness_files must include docker-compose.yml")
            return
        if len(compose_keys) > 1:
            self.warn(where, f"multiple docker-compose.yml files found: {compose_keys}")

        compose_content = harness_files.get(compose_keys[0])
        if not isinstance(compose_content, str) or not compose_content.strip():
            self.error(where, "docker-compose.yml content is empty")
            return
        try:
            compose = yaml.safe_load(compose_content)
        except yaml.YAMLError as exc:
            self.error(where, f"docker-compose.yml is not valid YAML: {exc}")
            return
        if not isinstance(compose, dict):
            self.error(where, "docker-compose.yml top level must be an object")
            return
        services = compose.get("services")
        if not isinstance(services, dict) or not services:
            self.error(where, "docker-compose.yml must define at least one service")
            return
        for service_name, service in services.items():
            if not isinstance(service, dict):
                self.error(where, f"service {service_name!r} must be an object")
                continue
            if not service.get("image") and not service.get("build"):
                self.error(where, f"service {service_name!r} has neither image nor build")

    def _validate_prompt_paths(
        self,
        where: str,
        input_items: Any,
        context_files: dict[str, str],
        harness_files: Any,
    ) -> None:
        if not isinstance(input_items, list) or len(input_items) < 2:
            return
        user_msg = input_items[1]
        if not isinstance(user_msg, dict):
            return
        prompt = user_msg.get("content")
        if not isinstance(prompt, str):
            return
        available = set(context_files)
        if isinstance(harness_files, dict):
            available.update(harness_files)

        missing: set[str] = set()
        for match in CODE_PATH_RE.finditer(prompt):
            rel = match.group(1)
            if rel in available:
                continue
            rel_no_external = rel.removeprefix("external/")
            if rel_no_external in available:
                continue
            path = PurePosixPath(rel)
            stem = str(path.with_suffix(""))
            swapped = {
                ".sv": ".v",
                ".v": ".sv",
                ".svh": ".vh",
                ".vh": ".svh",
            }.get(path.suffix)
            if swapped and f"{stem}{swapped}" in available:
                continue
            # New files the agent is asked to create are allowed; this is a warning.
            missing.add(rel)
        if missing:
            shown = sorted(missing)[:5]
            suffix = "" if len(missing) <= 5 else f" (+{len(missing) - 5} more)"
            self.warn(where, f"prompt references paths not present before rollout: {shown}{suffix}")

    def _validate_manifest(self) -> None:
        if self.manifest is None:
            return
        if not self.manifest.exists():
            self.error(str(self.manifest), "manifest not found")
            return
        try:
            manifest = json.loads(self.manifest.read_text())
            self._manifest_payload = manifest
        except json.JSONDecodeError as exc:
            self.error(str(self.manifest), f"manifest is invalid JSON: {exc}")
            return
        for item in manifest.get("cids", []):
            cid = item.get("cid")
            label = item.get("label")
            folder = self.data_root / f"{cid}_{label}"
            if not folder.exists():
                self.error(str(self.manifest), f"manifest folder missing: {folder}")
                continue
            if "materialized_all" in item:
                all_count = self.counts_by_split.get(f"{folder.name}/all.jsonl", 0)
                if all_count != item.get("materialized_all"):
                    self.error(str(self.manifest), f"{cid} all count mismatch: file={all_count}, manifest={item.get('materialized_all')}")
                continue
            train_count = self.counts_by_split.get(f"{folder.name}/train.jsonl", 0)
            test_count = self.counts_by_split.get(f"{folder.name}/test.jsonl", 0)
            if train_count != item.get("materialized_train"):
                self.error(str(self.manifest), f"{cid} train count mismatch: file={train_count}, manifest={item.get('materialized_train')}")
            if test_count != item.get("materialized_test"):
                self.error(str(self.manifest), f"{cid} test count mismatch: file={test_count}, manifest={item.get('materialized_test')}")
            if train_count + test_count != item.get("raw_total"):
                self.error(str(self.manifest), f"{cid} total split count does not match raw_total")

    def _validate_source_coverage(self) -> None:
        if self.source is None:
            return
        if not self.source.exists():
            self.error(str(self.source), "source file not found")
            return
        source_ids: set[str] = set()
        source_counts: Counter[str] = Counter()
        try:
            rows = list(_iter_source_rows(self.source))
        except (ValueError, json.JSONDecodeError) as exc:
            self.error(str(self.source), str(exc))
            return
        manifest_cids = self._manifest_selected_cids()
        manifest_task_ids = self._manifest_selected_task_ids()
        for row in rows:
            cid = next((c for c in row.get("categories", []) if isinstance(c, str) and c.startswith("cid")), "unknown")
            if manifest_cids and cid not in manifest_cids:
                continue
            task_id = row.get("id")
            if manifest_task_ids and task_id not in manifest_task_ids:
                continue
            if isinstance(task_id, str):
                source_ids.add(task_id)
            source_counts[cid] += 1

        generated_ids = set(self.task_locations)
        missing = source_ids - generated_ids
        extra = generated_ids - source_ids
        if missing:
            self.error(str(self.source), f"{len(missing)} source task IDs missing from generated splits")
        if extra:
            self.error(str(self.source), f"{len(extra)} generated task IDs not present in source")
        for cid, count in source_counts.items():
            generated = self.counts_by_cid.get(cid, 0)
            if generated != count:
                self.error(str(self.source), f"{cid} count mismatch: source={count}, generated={generated}")

    def _manifest_selected_cids(self) -> set[str]:
        """Return CIDs explicitly materialized by the manifest, if available.

        This keeps source-coverage validation useful for subset dry runs such
        as `--cids cid003`: omitted CIDs are intentionally absent, while every
        task from the selected CID still has to appear exactly once.
        """
        if self.manifest is None:
            return set()
        payload = self._manifest_payload
        if payload is None and self.manifest.exists():
            try:
                payload = json.loads(self.manifest.read_text())
            except json.JSONDecodeError:
                return set()
        if not isinstance(payload, dict):
            return set()
        return {
            str(item.get("cid"))
            for item in payload.get("cids", [])
            if isinstance(item, dict) and item.get("cid")
        }

    def _manifest_selected_task_ids(self) -> set[str]:
        """Return explicitly selected task IDs for subset manifests, if present."""
        if self.manifest is None:
            return set()
        payload = self._manifest_payload
        if payload is None and self.manifest.exists():
            try:
                payload = json.loads(self.manifest.read_text())
            except json.JSONDecodeError:
                return set()
        if not isinstance(payload, dict):
            return set()
        task_ids: set[str] = set()
        for item in payload.get("cids", []):
            if not isinstance(item, dict):
                continue
            for task_id in item.get("selected_task_ids", []):
                if isinstance(task_id, str):
                    task_ids.add(task_id)
        return task_ids

    @staticmethod
    def _safe_relpath(relpath: str) -> bool:
        if relpath.startswith("/") or "\x00" in relpath:
            return False
        parts = PurePosixPath(relpath).parts
        return ".." not in parts

    def _print_report(self) -> None:
        print("CVDP materialized data validation")
        print(f"data_root: {self.data_root}")
        print(f"rows: {len(self.rows)}")
        print("\nCounts by CID:")
        for cid in sorted(self.counts_by_cid):
            print(f"  {cid}: {self.counts_by_cid[cid]}")
        print("\nCounts by split:")
        for split in sorted(self.counts_by_split):
            print(f"  {split}: {self.counts_by_split[split]}")
        print(f"\nErrors: {len(self.errors)}")
        for error in self.errors[:80]:
            print(f"  ERROR {error}")
        if len(self.errors) > 80:
            print(f"  ... {len(self.errors) - 80} more errors")
        print(f"Warnings: {len(self.warnings)}")
        for warning in self.warnings[:40]:
            print(f"  WARN {warning}")
        if len(self.warnings) > 40:
            print(f"  ... {len(self.warnings) - 40} more warnings")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("nemogym/data"))
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args()

    manifest = args.manifest
    if manifest is None:
        candidate = args.data_root / "cid_splits_manifest.json"
        manifest = candidate if candidate.exists() else None

    return Validator(args.data_root, args.source, manifest).validate()


if __name__ == "__main__":
    sys.exit(main())
