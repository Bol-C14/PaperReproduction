#!/usr/bin/env python3
"""Download and verify only the public CVDP files used by Trace2Skill.

The repository intentionally stores no benchmark payloads or Git bundles. This
script pins the public Hugging Face dataset revision and retrieves one JSONL
file plus the seven bundles referenced by the eight paper tasks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_REPO = "nvidia/cvdp-benchmark-dataset"
DATASET_REVISION = "5b807d945f6a99aa645f7e43a64a2115e281b4bf"
BASE_URL = f"https://huggingface.co/datasets/{DATASET_REPO}/resolve/{DATASET_REVISION}"

# path -> (size in bytes, SHA-256)
FILES: dict[str, tuple[int, str]] = {
    "cvdp_v1.1.0_agentic_heavy_code_generation_no_commercial.jsonl": (
        1_405_895,
        "809916fa3248a4b2597b2a2ac364d3450d24936cad0e25bbe1bf0f1243ad1ea7",
    ),
    "cvdp_v1.1.0_agentic_heavy_code_generation_public/cvdp_agentic_heavy_802.11a.bundle": (
        2_333_570,
        "a26ac271d966bbd1f9f1aba96e37de9787fa0053e8c98a59f250f2149c69d31b",
    ),
    "cvdp_v1.1.0_agentic_heavy_code_generation_public/cvdp_agentic_heavy_NoobsCpu-8bit.bundle": (
        13_407_788,
        "56e05dc3fb07ccac09cefb15b16d060eb0ea760472b76c555de7ff5102fc34ef",
    ),
    "cvdp_v1.1.0_agentic_heavy_code_generation_public/cvdp_agentic_heavy_async-fifo.bundle": (
        1_035_758,
        "cdca16b076dba57a23d0bad06ddedcb6578234d3669d7068e7f33996187cc132",
    ),
    "cvdp_v1.1.0_agentic_heavy_code_generation_public/cvdp_agentic_heavy_fpga_nes.bundle": (
        1_302_283,
        "3119b8c47aa22ac6eb5714a4e869d014e8f85173cc746570d4d9029cc77d0de7",
    ),
    "cvdp_v1.1.0_agentic_heavy_code_generation_public/cvdp_agentic_heavy_rvx.bundle": (
        544_966,
        "e07e08d6273faf276a2c4bc120b084a5289d9b1c82ff567b49d3dc63ec0e8d49",
    ),
    "cvdp_v1.1.0_agentic_heavy_code_generation_public/cvdp_agentic_heavy_schoolMIPS.bundle": (
        9_848,
        "6678ed1708d5b19954014f876091f5015b5d30c395976825792e41c07e9a76cb",
    ),
    "cvdp_v1.1.0_agentic_heavy_code_generation_public/cvdp_agentic_heavy_verilog_pcie.bundle": (
        577_226,
        "9cc2d27756b8bb20d93d76a9cba117532801956a57172cdf8ff592f335010d8f",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid(path: Path, expected_size: int, expected_sha: str) -> bool:
    return path.is_file() and path.stat().st_size == expected_size and sha256(path) == expected_sha


def download(relative_path: str, destination: Path, expected_size: int, expected_sha: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    request = urllib.request.Request(
        f"{BASE_URL}/{relative_path}",
        headers={"User-Agent": "Trace2Skill/1.0 public artifact downloader"},
    )
    print(f"download {relative_path} ({expected_size / 1_000_000:.2f} MB)")
    try:
        with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        if not valid(partial, expected_size, expected_sha):
            actual_size = partial.stat().st_size if partial.exists() else -1
            actual_sha = sha256(partial) if partial.exists() else "missing"
            raise RuntimeError(
                f"integrity failure for {relative_path}: "
                f"size={actual_size}, sha256={actual_sha}"
            )
        os.replace(partial, destination)
    finally:
        if partial.exists():
            partial.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        type=Path,
        default=REPO_ROOT / "data" / "cvdp-v1.1.0",
        help="Download root (default: data/cvdp-v1.1.0).",
    )
    parser.add_argument("--check-only", action="store_true", help="Verify existing files without network access.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    destination_root = args.dest.expanduser().resolve()
    failures: list[str] = []
    for relative_path, (expected_size, expected_sha) in FILES.items():
        destination = destination_root / relative_path
        if valid(destination, expected_size, expected_sha):
            print(f"ok       {relative_path}")
            continue
        if args.check_only:
            failures.append(relative_path)
            print(f"missing/invalid {relative_path}", file=sys.stderr)
            continue
        download(relative_path, destination, expected_size, expected_sha)
        print(f"verified {relative_path}")

    if failures:
        return 1

    if args.check_only:
        print(f"CVDP SUBSET VERIFIED: {destination_root}")
        return 0

    manifest = {
        "dataset_repo": DATASET_REPO,
        "dataset_revision": DATASET_REVISION,
        "files": [
            {"path": path, "size": size, "sha256": digest}
            for path, (size, digest) in FILES.items()
        ],
    }
    destination_root.mkdir(parents=True, exist_ok=True)
    manifest_path = destination_root / "trace2skill_download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"CVDP SUBSET READY: {destination_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
