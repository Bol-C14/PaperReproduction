from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from run_optimizer import (  # noqa: E402
    validate_mutated_skill,
    write_mutation_health_record,
)


def _parent_skill() -> str:
    return """# CID Skill

- Read the target RTL with cat before editing.
- Prefer edit over echo for existing files.
- Verify with iverilog and vvp after changes.
""" * 12


def test_validate_mutated_skill_rejects_empty_and_unchanged() -> None:
    parent = _parent_skill()

    empty = validate_mutated_skill("", parent, max_chars=12000)
    assert not empty["ok"]
    assert "empty_output" in empty["issues"]

    unchanged = validate_mutated_skill(parent, parent, max_chars=12000)
    assert not unchanged["ok"]
    assert "unchanged_exact" in unchanged["issues"]


def test_validate_mutated_skill_rejects_error_text() -> None:
    parent = _parent_skill()
    candidate = "# Skill\n\nInternalServerError: service unavailable. Please retry later."

    result = validate_mutated_skill(candidate, parent, max_chars=12000)

    assert not result["ok"]
    assert "looks_like_error_or_refusal" in result["issues"]


def test_validate_mutated_skill_accepts_skill_like_revision() -> None:
    parent = _parent_skill()
    candidate = """# CID Skill

## Workflow

- Read the task and identify the exact RTL file named by the verifier.
- Use cat on the target file before any edit.
- Prefer edit for surgical replacements in existing files.
- Use echo only for brand-new files.
- Run iverilog with the provided harness, then run vvp on the generated output.
- If validation fails, inspect the first concrete compile or assertion error before editing again.

## Avoid

- Do not invent a parallel testbench when the task already provides one.
- Do not leave the modified file unread after writing it.
"""

    result = validate_mutated_skill(candidate, parent, max_chars=12000)

    assert result["ok"]
    assert result["issues"] == []
    assert result["metrics"]["candidate_chars"] > 300


def test_write_mutation_health_record_writes_root_and_generation(tmp_path: Path) -> None:
    payload = write_mutation_health_record(
        tmp_path,
        2,
        {
            "status": "invalid_output",
            "ok": False,
            "next_generation": 3,
            "child_slot": 0,
            "mutation_model": "synthetic-model",
            "issues": ["empty_output"],
            "metrics": {"parent_chars": 1000, "candidate_chars": 0},
        },
    )

    assert payload["generation"] == 2
    root_lines = (tmp_path / "mutation_health.jsonl").read_text().splitlines()
    gen_lines = (tmp_path / "gen2" / "mutation_health.jsonl").read_text().splitlines()
    assert len(root_lines) == 1
    assert len(gen_lines) == 1
    assert json.loads(root_lines[0])["issues"] == ["empty_output"]
