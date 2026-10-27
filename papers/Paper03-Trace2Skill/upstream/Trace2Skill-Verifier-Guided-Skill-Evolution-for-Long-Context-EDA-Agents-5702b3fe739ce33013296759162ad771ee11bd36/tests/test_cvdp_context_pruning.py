import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
NEMOGYM_ROOT = REPO_ROOT / "nemogym"
if str(NEMOGYM_ROOT) not in sys.path:
    sys.path.insert(0, str(NEMOGYM_ROOT))

from nemo_gym.server_utils import SESSION_ID_KEY, ServerClient
from resources_servers.cvdp_agentic_heavy.app import (
    CVDPAgenticHeavyConfig,
    CVDPAgenticHeavyResourcesServer,
    SessionState,
    ToolRequest,
)
from resources_servers.cvdp_agentic_heavy.context_pruning import (
    CONTEXT_MANIFEST_FILE,
    CONTEXT_PRUNING_META_KEY,
    apply_pruning_to_row,
)


def _row(prompt: str = "Fix /code/rtl/top.v") -> dict:
    return {
        "responses_create_params": {
            "input": [
                {"role": "developer", "content": "Use tools."},
                {"role": "user", "content": prompt},
            ],
            "tools": [],
        },
        "verifier_metadata": {
            "task_id": "cvdp_agentic_heavy_demo_0001",
            "categories": ["cid016", "hard"],
            "difficulty": "hard",
            "context_files": {
                "rtl/top.v": "module top; endmodule\n",
                "tb/top_tb.sv": "module top_tb; endmodule\n",
                "README.md": "# demo\n",
                "layout/top.gds": "G" * 1000,
                "output/build.log": "old generated log\n",
                "programs/boot.hex": "aa\n" * 200,
            },
            "harness_files": {"docker-compose.yml": "services: {}\n"},
            "patch": {},
            "origin": {},
        },
    }


def _cfg(**kw):
    data = {
        "host": "0.0.0.0",
        "port": 8080,
        "entrypoint": "",
        "name": "ah",
        "num_processes": 1,
        "docker_timeout": 30,
        "tool_timeout": 30,
    }
    data.update(kw)
    return CVDPAgenticHeavyConfig(**data)


def _srv():
    return CVDPAgenticHeavyResourcesServer(config=_cfg(), server_client=MagicMock(spec=ServerClient))


def _req(sid: str = "s1"):
    request = MagicMock()
    request.session = {SESSION_ID_KEY: sid}
    return request


def test_pruning_keeps_source_and_makes_pruned_files_restorable(tmp_path):
    store_path = tmp_path / "store.json"
    pruned_row, store_payload, result = apply_pruning_to_row(
        _row(),
        store_path=str(store_path),
        max_non_source_bytes=100,
        max_small_text_bytes=100,
    )

    context_files = pruned_row["verifier_metadata"]["context_files"]
    assert "rtl/top.v" in context_files
    assert "tb/top_tb.sv" in context_files
    assert "layout/top.gds" not in context_files
    assert "output/build.log" not in context_files
    assert "programs/boot.hex" not in context_files
    assert CONTEXT_MANIFEST_FILE in context_files
    assert "restore_file" in context_files[CONTEXT_MANIFEST_FILE]

    tools = pruned_row["responses_create_params"]["tools"]
    assert any(tool.get("name") == "edit" for tool in tools)
    assert any(tool.get("name") == "restore_file" for tool in tools)
    assert "CONTEXT PRUNING ABLATION" in pruned_row["responses_create_params"]["input"][0]["content"]

    pruning_meta = pruned_row["verifier_metadata"][CONTEXT_PRUNING_META_KEY]
    assert pruning_meta["enabled"] is True
    assert pruning_meta["store_path"] == str(store_path)
    assert pruning_meta["pruned_file_count"] == len(result.pruned_files)

    assert "layout/top.gds" in store_payload["files"]
    assert "programs/boot.hex" in store_payload["files"]


def test_explicitly_referenced_large_file_is_kept(tmp_path):
    row = _row(prompt="The failing program is /code/programs/boot.hex; inspect it before editing rtl/top.v.")
    pruned_row, store_payload, _ = apply_pruning_to_row(
        row,
        store_path=str(tmp_path / "store.json"),
        max_non_source_bytes=100,
        max_small_text_bytes=100,
    )

    context_files = pruned_row["verifier_metadata"]["context_files"]
    assert "programs/boot.hex" in context_files
    assert "programs/boot.hex" not in store_payload["files"]


def test_pruning_drops_hidden_verifier_files_even_if_referenced(tmp_path):
    row = _row(prompt="Do not use /code/harness/1/src/test_runner.py; fix /code/rtl/top.v.")
    row["verifier_metadata"]["context_files"].update(
        {
            "harness/1/src/test_runner.py": "hidden runner\n",
            "harness.py": "hidden helper\n",
            "nested/test_runner.py": "hidden helper\n",
        }
    )

    pruned_row, store_payload, _ = apply_pruning_to_row(
        row,
        store_path=str(tmp_path / "store.json"),
        max_non_source_bytes=100,
        max_small_text_bytes=100,
    )

    context_files = pruned_row["verifier_metadata"]["context_files"]
    assert "harness/1/src/test_runner.py" not in context_files
    assert "harness.py" not in context_files
    assert "nested/test_runner.py" not in context_files
    assert "harness/1/src/test_runner.py" not in store_payload["files"]
    assert "harness.py" not in store_payload["files"]
    assert "nested/test_runner.py" not in store_payload["files"]


@pytest.mark.asyncio
async def test_restore_file_recovers_exact_sidecar_content(tmp_path):
    store_path = tmp_path / "store.json"
    store_path.write_text(
        json.dumps({"version": "test", "task_id": "t1", "files": {"programs/boot.hex": "aa\nbb\n"}}),
        encoding="utf-8",
    )

    srv = _srv()
    sid = "restore"
    srv._sessions[sid] = SessionState(sandbox=tmp_path / "sandbox", container_id="", restore_store_path=store_path)
    srv._sessions[sid].sandbox.mkdir()

    response = await srv.tool_restore_file(_req(sid), ToolRequest(filename="programs/boot.hex"))

    assert "Restored programs/boot.hex" in response.output
    assert (tmp_path / "sandbox" / "programs" / "boot.hex").read_text() == "aa\nbb\n"


@pytest.mark.asyncio
async def test_restore_file_rejects_path_escape(tmp_path):
    store_path = tmp_path / "store.json"
    store_path.write_text(json.dumps({"files": {"safe.txt": "ok"}}), encoding="utf-8")

    srv = _srv()
    sid = "restore"
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    srv._sessions[sid] = SessionState(sandbox=sandbox, container_id="", restore_store_path=store_path)

    response = await srv.tool_restore_file(_req(sid), ToolRequest(filename="../../escape.txt"))

    assert "Error: path escapes sandbox" in response.output
    assert not (tmp_path / "escape.txt").exists()
