#!/usr/bin/env python3
"""Reject common secret, restricted-data, path, and oversized-file mistakes."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 10 * 1024 * 1024
FORBIDDEN_SUFFIXES = {".bundle", ".vcd", ".vvp", ".fst", ".tar", ".oci"}
FORBIDDEN_PATH_PARTS = {"envs", "runs", "outputs", "cache", "__pycache__"}
TEXT_PATTERNS = {
    "private absolute path": re.compile(r"/(?:home|mnt)/(?:[^/\s]+/){1,}"),
    "internal domain": re.compile(r"(?:gitlab-master|inference-api)\.nvidia\.com", re.I),
    "confidential marker": re.compile(r"NVIDIA\s+Confidential", re.I),
    "private-key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "API token": re.compile(r"(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
}


def candidate_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]


def main() -> int:
    errors: list[str] = []
    files = candidate_files()

    for path in files:
        rel = path.relative_to(ROOT)
        if path.is_symlink():
            errors.append(f"symlink is not allowed: {rel}")
            continue
        if not path.is_file():
            continue
        if path.stat().st_size > MAX_BYTES:
            errors.append(f"file exceeds 10 MiB: {rel} ({path.stat().st_size} bytes)")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden generated/archive suffix: {rel}")
        if any(part in FORBIDDEN_PATH_PARTS for part in rel.parts):
            errors.append(f"forbidden generated path: {rel}")
        if path.name == ".env":
            errors.append(f"credential file is tracked: {rel}")
        if path.stat().st_size > 2 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in TEXT_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label}: {rel}")

    required_license_files = (
        "LICENSE",
        "nemogym/LICENSE",
        "CVDP_DATASET_LICENSE",
        "CVDP_DATASET_NOTICE",
    )
    for relative_path in required_license_files:
        if not (ROOT / relative_path).is_file():
            errors.append(f"required license file is missing: {relative_path}")

    if errors:
        print("PUBLIC RELEASE CHECK FAILED", file=sys.stderr)
        for error in sorted(set(errors)):
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"PUBLIC RELEASE CHECK PASSED: {len(files)} files, no file over 10 MiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
