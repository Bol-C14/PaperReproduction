from __future__ import annotations

import importlib.util
import gzip
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


convert_to_gym = _load_module(
    "cvdp_convert_to_gym",
    "nemogym/resources_servers/cvdp_agentic_heavy/scripts/convert_to_gym.py",
)
validate_cvdp = _load_module("validate_cvdp_materialized", "scripts/validate_cvdp_materialized.py")


def test_converter_filters_hidden_verifier_paths_and_python_tests() -> None:
    files = {
        "rtl/top.v": "module top; endmodule\n",
        "tb/top_tb.sv": "module top_tb; endmodule\n",
        "tb/test_top.py": "def test_top(): pass\n",
        "harness/1/src/test_runner.py": "hidden runner\n",
        "harness.py": "hidden helper\n",
        "nested/test_runner.py": "hidden helper\n",
    }

    assert convert_to_gym.is_hidden_verifier_path("harness/1/src/test_runner.py")
    assert convert_to_gym.is_hidden_verifier_path("nested/test_runner.py")
    assert not convert_to_gym.is_hidden_verifier_path("tb/top_tb.sv")

    assert convert_to_gym.find_visible_verilog_testbenches(files) == ["tb/top_tb.sv"]


def test_testbench_hint_is_conservative_when_explicitly_enabled() -> None:
    prompt = convert_to_gym.enrich_prompt_with_testbenches("Do the task.", ["tb/top_tb.sv"], "demo")

    assert "VISIBLE VERILOG/SYSTEMVERILOG VERIFICATION FILES" in prompt
    assert "AVAILABLE TESTBENCHES" not in prompt
    assert "iverilog(args=" not in prompt
    assert "tb/top_tb.sv" in prompt


def test_converter_reads_gzipped_v110_jsonl(tmp_path: Path) -> None:
    source = tmp_path / "tasks.jsonl.gz"
    row = {
        "id": "cvdp_agentic_heavy_demo_0001",
        "categories": ["cid016", "hard"],
        "prompt": "Fix /code/rtl/top.v",
        "context": {"repo": "cvdp_agentic_heavy_demo", "commit": "abc123"},
        "origin": {},
        "patch": {},
        "harness": {"docker-compose.yml": "services: {verif: {image: test}}\n"},
    }
    with gzip.open(source, "wt", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

    rows = list(convert_to_gym.iter_json_rows(source))

    assert rows == [row]


def test_v110_bundle_repo_resolution_prefers_directory_then_bundle(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundles"
    bundle_root.mkdir()
    repo_dir = bundle_root / "cvdp_agentic_heavy_demo"
    repo_dir.mkdir()
    bundle = bundle_root / "cvdp_agentic_heavy_other.bundle"
    bundle.write_text("bundle placeholder\n")

    assert convert_to_gym.resolve_heavy_repo_reference("cvdp_agentic_heavy_demo", str(bundle_root)) == str(repo_dir)
    assert convert_to_gym.resolve_heavy_repo_reference("cvdp_agentic_heavy_other", str(bundle_root)) == str(bundle)
    assert convert_to_gym.resolve_heavy_repo_reference("https://example/repo.git", str(bundle_root)) == "https://example/repo.git"


def test_convert_entry_preserves_v110_source_context_in_skip_resolve() -> None:
    row = {
        "id": "cvdp_agentic_heavy_demo_0001",
        "categories": ["cid016", "hard"],
        "prompt": "Fix /code/rtl/top.v",
        "context": {"repo": "cvdp_agentic_heavy_demo", "commit": "abc123"},
        "origin": {"repo": "upstream", "commit": "def456"},
        "patch": {"rtl/top.v": ""},
        "harness": {"files": {"docker-compose.yml": "services: {verif: {image: test}}\n"}},
    }

    out = convert_to_gym.convert_entry(row, str(ROOT), True, "skill text " * 20)

    meta = out["verifier_metadata"]
    assert meta["source_context"] == row["context"]
    assert meta["harness_files"] == row["harness"]["files"]
    assert meta["context_files"]["SKILL.md"].startswith("skill text")


def test_convert_entry_keeps_verify_feedback_absent_by_default() -> None:
    row = {
        "id": "cvdp_agentic_heavy_demo_0001",
        "categories": ["cid016", "hard"],
        "prompt": "Fix /code/rtl/top.v",
        "context": {"repo": "cvdp_agentic_heavy_demo", "commit": "abc123"},
        "origin": {},
        "patch": {},
        "harness": {"files": {"docker-compose.yml": "services: {verif: {image: test}}\n"}},
    }

    out = convert_to_gym.convert_entry(row, str(ROOT), True, "skill text " * 20)

    tools = [tool["name"] for tool in out["responses_create_params"]["tools"]]
    prompt = out["responses_create_params"]["input"][0]["content"]
    skill = out["verifier_metadata"]["context_files"]["SKILL.md"]
    assert "verify_feedback" not in tools
    assert "verify_feedback(reason)" not in prompt
    assert "verify_feedback(reason)" not in skill


def test_convert_entry_can_enable_verify_feedback_explicitly() -> None:
    row = {
        "id": "cvdp_agentic_heavy_demo_0001",
        "categories": ["cid016", "hard"],
        "prompt": "Fix /code/rtl/top.v",
        "context": {"repo": "cvdp_agentic_heavy_demo", "commit": "abc123"},
        "origin": {},
        "patch": {},
        "harness": {"files": {"docker-compose.yml": "services: {verif: {image: test}}\n"}},
    }

    out = convert_to_gym.convert_entry(
        row,
        str(ROOT),
        True,
        "skill text " * 20,
        enable_verify_feedback_tool=True,
    )

    tools = [tool["name"] for tool in out["responses_create_params"]["tools"]]
    prompt = out["responses_create_params"]["input"][0]["content"]
    skill = out["verifier_metadata"]["context_files"]["SKILL.md"]
    assert "verify_feedback" in tools
    assert "verify_feedback(reason)" in prompt
    assert "verify_feedback(reason)" in skill


def test_materialized_validator_flags_stale_harness_guidance() -> None:
    validator = validate_cvdp.Validator(Path("."), None, None)
    validator._validate_prompt_hygiene(
        "row1",
        [
            {
                "role": "developer",
                "content": (
                    "AVAILABLE TESTBENCHES in this project:\n"
                    "- harness/1/src/test_runner.py\n"
                    'iverilog(args="-o sim.vvp -g2012 rtl/top.v harness/1/src/test_runner.py")'
                ),
            }
        ],
    )
    validator._validate_context(
        "row1",
        {
            "SKILL.md": "x" * 200,
            "rtl/top.v": "module top; endmodule\n",
            "harness/1/src/test_runner.py": "hidden runner\n",
        },
    )

    assert any("deprecated generated testbench hint" in err for err in validator.errors)
    assert any("Python/cocotb/pytest file to iverilog" in err for err in validator.errors)
    assert any("hidden verifier/harness path" in err for err in validator.errors)
