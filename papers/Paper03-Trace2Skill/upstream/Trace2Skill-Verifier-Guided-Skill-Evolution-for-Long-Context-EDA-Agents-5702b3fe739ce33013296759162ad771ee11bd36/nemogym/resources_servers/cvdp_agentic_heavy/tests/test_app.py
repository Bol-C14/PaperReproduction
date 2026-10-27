# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import shutil
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from nemo_gym.server_utils import ServerClient, SESSION_ID_KEY
from resources_servers.cvdp_agentic_heavy.app import (
    CVDPAgenticHeavyResourcesServer,
    CVDPAgenticHeavyConfig,
    CVDPAgenticHeavyVerifyRequest,
    SessionState,
    ToolRequest,
    VerifyFeedbackRequest,
    _apply_substitutions,
    _filter_code_volumes,
)

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

SV = "module foo(input clk);\nendmodule"
COMPOSE = "services:\n  direct:\n    image: __OSS_SIM_IMAGE__\n    command: echo done\n"
HARNESS = {"docker-compose.yml": COMPOSE, "src/.env": "SIM=icarus\n"}
CTX = {"rtl/foo.sv": SV, "rtl/bar.sv": "module bar;\nendmodule", "docs/spec.md": "# Spec"}
META = {
    "task_id": "t1",
    "categories": ["cid016", "hard"],
    "difficulty": "hard",
    "context_files": CTX,
    "harness_files": HARNESS,
    "patch": {},
    "origin": {},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cfg(**kw):
    d = dict(
        host="0.0.0.0", port=8080, entrypoint="", name="ah",
        num_processes=1, docker_timeout=30, tool_timeout=30,
    )
    d.update(kw)
    return CVDPAgenticHeavyConfig(**d)


def _srv(**kw):
    return CVDPAgenticHeavyResourcesServer(
        config=_cfg(**kw), server_client=MagicMock(spec=ServerClient),
    )


def _req(sid="s1"):
    r = MagicMock()
    r.session = {SESSION_ID_KEY: sid}
    return r


def _vbody(sid="s1"):
    bd = {
        "responses_create_params": {"input": [{"role": "user", "content": "fix"}]},
        "response": {
            "id": "resp_test",
            "created_at": 1000000,
            "model": "test-model",
            "object": "response",
            "output": [
                {
                    "type": "message",
                    "id": "msg_test",
                    "role": "assistant",
                    "status": "completed",
                    "content": [{"type": "output_text", "text": "ok", "annotations": []}],
                },
            ],
            "parallel_tool_calls": True,
            "tool_choice": "auto",
            "tools": [],
            "usage": {
                "input_tokens": 1,
                "output_tokens": 1,
                "total_tokens": 2,
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens_details": {"reasoning_tokens": 0},
            },
        },
        "verifier_metadata": META,
    }
    return _req(sid), CVDPAgenticHeavyVerifyRequest.model_validate(bd)


def _setup_sandbox(srv, sid="s1"):
    sb = Path(tempfile.mkdtemp())
    (sb / "rtl").mkdir()
    (sb / "rtl" / "foo.sv").write_text(SV)
    (sb / "rtl" / "bar.sv").write_text("module bar;\nendmodule")
    (sb / "docs").mkdir()
    (sb / "docs" / "spec.md").write_text("# Spec")
    srv._sessions[sid] = SessionState(
        sandbox=sb,
        container_id="",
        original_files=CTX,
        verifier_metadata=META,
        feedback_artifact_dir=sb.parent / "feedback_artifacts",
    )
    return sb


# ---------------------------------------------------------------------------
# Tests: _apply_substitutions
# ---------------------------------------------------------------------------


class TestApplySubstitutions:
    def test_oss_sim(self):
        assert "cvdp-sim" in _apply_substitutions("__OSS_SIM_IMAGE__", _cfg())

    def test_oss_pnr(self):
        assert "cvdp-sim" in _apply_substitutions("__OSS_PNR_IMAGE__", _cfg())

    def test_eda_when_set(self):
        assert "xc" in _apply_substitutions("__VERIF_EDA_IMAGE__", _cfg(eda_sim_image="xc"))

    def test_eda_when_empty(self):
        assert "__VERIF" in _apply_substitutions("__VERIF_EDA_IMAGE__", _cfg())

    def test_noop(self):
        assert _apply_substitutions("hello", _cfg()) == "hello"


# ---------------------------------------------------------------------------
# Tests: _filter_code_volumes
# ---------------------------------------------------------------------------


class TestFilterCodeVolumes:
    def test_removes_code_volumes(self):
        c = "services:\n  s:\n    volumes:\n      - /code/x:/y\n      - ./src:/src\n"
        d = yaml.safe_load(_filter_code_volumes(c))
        assert not any("/code" in v for v in d["services"]["s"]["volumes"])

    def test_keeps_non_code(self):
        c = "services:\n  s:\n    volumes:\n      - ./src:/src\n"
        d = yaml.safe_load(_filter_code_volumes(c))
        assert any("/src" in v for v in d["services"]["s"]["volumes"])

    def test_no_volumes(self):
        c = "services:\n  s:\n    command: echo\n"
        assert "echo" in _filter_code_volumes(c)


# ---------------------------------------------------------------------------
# Tests: tool_ls
# ---------------------------------------------------------------------------


class TestToolLs:
    def setup_method(self):
        self.srv = _srv()
        self.sb = _setup_sandbox(self.srv)

    def teardown_method(self):
        shutil.rmtree(self.sb, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_root(self):
        r = await self.srv.tool_ls(_req(), ToolRequest(path="."))
        assert "rtl" in r.output

    @pytest.mark.asyncio
    async def test_subdir(self):
        r = await self.srv.tool_ls(_req(), ToolRequest(path="rtl"))
        assert "foo.sv" in r.output
        assert "bar.sv" in r.output

    @pytest.mark.asyncio
    async def test_missing_dir(self):
        r = await self.srv.tool_ls(_req(), ToolRequest(path="nope"))
        assert "Error" in r.output

    @pytest.mark.asyncio
    async def test_path_escape(self):
        r = await self.srv.tool_ls(_req(), ToolRequest(path="../../etc"))
        assert "Error" in r.output


# ---------------------------------------------------------------------------
# Tests: tool_cat
# ---------------------------------------------------------------------------


class TestToolCat:
    def setup_method(self):
        self.srv = _srv()
        self.sb = _setup_sandbox(self.srv)

    def teardown_method(self):
        shutil.rmtree(self.sb, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_read_file(self):
        r = await self.srv.tool_cat(_req(), ToolRequest(filename="rtl/foo.sv"))
        assert "module foo" in r.output

    @pytest.mark.asyncio
    async def test_missing_file(self):
        r = await self.srv.tool_cat(_req(), ToolRequest(filename="nope.sv"))
        assert "Error" in r.output

    @pytest.mark.asyncio
    async def test_no_filename(self):
        r = await self.srv.tool_cat(_req(), ToolRequest())
        assert "Error" in r.output

    @pytest.mark.asyncio
    async def test_path_escape(self):
        r = await self.srv.tool_cat(_req(), ToolRequest(filename="../../etc/passwd"))
        assert "Error" in r.output


# ---------------------------------------------------------------------------
# Tests: diagnostic read/search/index tools
# ---------------------------------------------------------------------------


class TestDiagnosticTools:
    def setup_method(self):
        self.srv = _srv()
        self.sb = _setup_sandbox(self.srv)

    def teardown_method(self):
        shutil.rmtree(self.sb, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_rg_searches_visible_files(self):
        r = await self.srv.tool_rg(_req(), ToolRequest(pattern="module foo", path=".", glob="*.sv"))
        assert "rtl/foo.sv:1" in r.output
        assert "module foo" in r.output

    @pytest.mark.asyncio
    async def test_find_files_by_glob(self):
        r = await self.srv.tool_find_files(_req(), ToolRequest(path=".", glob="rtl/*.sv"))
        assert "rtl/foo.sv" in r.output
        assert "rtl/bar.sv" in r.output

    @pytest.mark.asyncio
    async def test_read_file_line_range(self):
        r = await self.srv.tool_read_file(_req(), ToolRequest(filename="rtl/foo.sv", start_line=1, end_line=1))
        assert "rtl/foo.sv:1-1" in r.output
        assert "1 | module foo" in r.output

    @pytest.mark.asyncio
    async def test_show_changes_diffs_against_original_visible_context(self):
        await self.srv.tool_edit(
            _req(),
            ToolRequest(filename="rtl/foo.sv", old_text="module foo", new_text="module foo_fixed"),
        )
        r = await self.srv.tool_show_changes(_req(), ToolRequest(filename="rtl/foo.sv", max_files=5))
        assert "--- original/rtl/foo.sv" in r.output
        assert "+++ current/rtl/foo.sv" in r.output
        assert "foo_fixed" in r.output

    @pytest.mark.asyncio
    async def test_module_index_lists_visible_modules(self):
        r = await self.srv.tool_module_index(_req(), ToolRequest(path="rtl"))
        assert "rtl/foo.sv:1: module foo" in r.output
        assert "rtl/bar.sv:1: module bar" in r.output

    @pytest.mark.asyncio
    async def test_diagnostic_tools_reject_path_escape(self):
        r = await self.srv.tool_find_files(_req(), ToolRequest(path="../../etc", glob="*"))
        assert "Error" in r.output


# ---------------------------------------------------------------------------
# Tests: tool_echo
# ---------------------------------------------------------------------------


class TestToolEcho:
    def setup_method(self):
        self.srv = _srv()
        self.sb = _setup_sandbox(self.srv)

    def teardown_method(self):
        shutil.rmtree(self.sb, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_create_file(self):
        r = await self.srv.tool_echo(
            _req(), ToolRequest(content="module x;\nendmodule", filename="rtl/x.sv"),
        )
        assert "Written" in r.output
        assert (self.sb / "rtl" / "x.sv").exists()
        assert "module x" in (self.sb / "rtl" / "x.sv").read_text()

    @pytest.mark.asyncio
    async def test_overwrite_file(self):
        (self.sb / "t.txt").write_text("old")
        await self.srv.tool_echo(_req(), ToolRequest(content="new", filename="t.txt"))
        assert (self.sb / "t.txt").read_text() == "new"

    @pytest.mark.asyncio
    async def test_creates_parent_dirs(self):
        await self.srv.tool_echo(_req(), ToolRequest(content="d", filename="a/b/c.txt"))
        assert (self.sb / "a" / "b" / "c.txt").exists()

    @pytest.mark.asyncio
    async def test_no_filename(self):
        r = await self.srv.tool_echo(_req(), ToolRequest(content="x"))
        assert "Error" in r.output

    @pytest.mark.asyncio
    async def test_path_escape(self):
        r = await self.srv.tool_echo(
            _req(), ToolRequest(content="x", filename="../../bad"),
        )
        assert "Error" in r.output


# ---------------------------------------------------------------------------
# Tests: tool_pwd
# ---------------------------------------------------------------------------


class TestToolPwd:
    def setup_method(self):
        self.srv = _srv()
        self.sb = _setup_sandbox(self.srv)

    def teardown_method(self):
        shutil.rmtree(self.sb, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_returns_code(self):
        r = await self.srv.tool_pwd(_req(), ToolRequest())
        assert r.output == "/code"


# ---------------------------------------------------------------------------
# Tests: no session error
# ---------------------------------------------------------------------------


class TestNoSession:
    @pytest.mark.asyncio
    async def test_tool_without_session_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await _srv().tool_ls(_req("bad"), ToolRequest(path="."))
        assert exc_info.value.status_code == 400
        assert "No session" in str(exc_info.value.detail)


# ---------------------------------------------------------------------------
# Tests: verify
# ---------------------------------------------------------------------------


class TestVerify:
    def setup_method(self):
        self.srv = _srv()

    @pytest.mark.asyncio
    async def test_no_sandbox_returns_zero(self):
        req, body = _vbody("bad")
        r = await self.srv.verify(req, body)
        assert r.reward == 0.0
        assert r.docker_exit_code == 1

    @pytest.mark.asyncio
    async def test_docker_pass(self):
        _setup_sandbox(self.srv)
        req, body = _vbody()
        with patch.object(
            self.srv, "_run_docker_harness",
            new_callable=AsyncMock, return_value=(0, "", []),
        ):
            r = await self.srv.verify(req, body)
        assert r.reward == 1.0
        assert r.task_id == "t1"
        assert r.category == "cid016"
        assert r.difficulty == "hard"

    @pytest.mark.asyncio
    async def test_docker_fail(self):
        _setup_sandbox(self.srv)
        req, body = _vbody()
        with patch.object(
            self.srv, "_run_docker_harness",
            new_callable=AsyncMock, return_value=(1, "FAIL", []),
        ):
            r = await self.srv.verify(req, body)
        assert r.reward == 0.0
        assert r.docker_exit_code == 1

    @pytest.mark.asyncio
    async def test_cleans_up_session(self):
        _setup_sandbox(self.srv)
        req, body = _vbody()
        with patch.object(
            self.srv, "_run_docker_harness",
            new_callable=AsyncMock, return_value=(0, "", []),
        ):
            await self.srv.verify(req, body)
        assert "s1" not in self.srv._sessions


# ---------------------------------------------------------------------------
# Tests: end-to-end (seed -> tools -> verify, Docker mocked)
# ---------------------------------------------------------------------------


class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_full_episode(self):
        srv = _srv()
        sid = "e2e"
        req = _req(sid)

        # Seed: create sandbox with context files
        sb = _setup_sandbox(srv, sid)

        # Agent reads a file
        r = await srv.tool_cat(req, ToolRequest(filename="rtl/foo.sv"))
        assert "module foo" in r.output

        # Agent lists directory
        r = await srv.tool_ls(req, ToolRequest(path="rtl"))
        assert "foo.sv" in r.output
        assert "bar.sv" in r.output

        # Agent writes a fix
        fixed = "module foo_fixed(input clk);\nendmodule"
        r = await srv.tool_echo(req, ToolRequest(content=fixed, filename="rtl/foo.sv"))
        assert "Written" in r.output
        assert "foo_fixed" in (sb / "rtl" / "foo.sv").read_text()

        # Verify (Docker mocked)
        vreq, vbody = _vbody(sid)
        with patch.object(
            srv, "_run_docker_harness",
            new_callable=AsyncMock, return_value=(0, "", []),
        ):
            r = await srv.verify(vreq, vbody)

        assert r.reward == 1.0
        assert sid not in srv._sessions


# ---------------------------------------------------------------------------
# Tests: runtime dense verifier feedback
# ---------------------------------------------------------------------------


class TestRuntimeVerifierFeedback:
    @pytest.mark.asyncio
    async def test_disabled_by_default(self):
        srv = _srv()
        _setup_sandbox(srv)
        r = await srv.tool_verify_feedback(_req(), VerifyFeedbackRequest(reason="debug failing tests"))
        payload = json.loads(r.output)
        assert payload["error"] == "verify_feedback_disabled"

    @pytest.mark.asyncio
    async def test_rejects_until_edit_and_successful_iverilog(self):
        srv = _srv(runtime_verifier_feedback_enabled=True)
        _setup_sandbox(srv)
        r = await srv.tool_verify_feedback(_req(), VerifyFeedbackRequest(reason="need functional signal"))
        assert json.loads(r.output)["error"] == "verify_feedback_requires_edit"

        session = srv._sessions["s1"]
        session.write_count = 1
        r = await srv.tool_verify_feedback(_req(), VerifyFeedbackRequest(reason="after edit"))
        assert json.loads(r.output)["error"] == "verify_feedback_requires_successful_iverilog"

    @pytest.mark.asyncio
    async def test_private_harness_sanitized_feedback_and_budget(self):
        srv = _srv(
            runtime_verifier_feedback_enabled=True,
            runtime_verifier_feedback_max_calls=1,
        )
        sb = _setup_sandbox(srv)
        session = srv._sessions["s1"]
        session.write_count = 1
        session.last_successful_compile_write_count = 1

        raw = (
            "TESTS=5 PASS=1 FAIL=4\n"
            "AssertionError: Output bit 1 failed: expected 0, got 1\n"
            "FAILED ../../src/test_runner.py::test_output_mismatch[0]\n"
            "File /src/test_runner.py, line 9, in hidden_test\n"
            "docker-compose.yml hidden harness detail\n"
        )
        async def fake_harness_service(workdir: str, service: str, task_id: str):
            Path(workdir, "dump.vcd").write_text(
                "\n".join([
                    "$timescale 1 ns $end",
                    "$scope module top $end",
                    "$var wire 1 ! clk $end",
                    "$var wire 1 \" rst_n $end",
                    "$var wire 1 # out_valid $end",
                    "$var wire 1 $ expected_value $end",
                    "$var wire 2 % state [1:0] $end",
                    "$upscope $end",
                    "$enddefinitions $end",
                    "#0",
                    "0!",
                    "0\"",
                    "0#",
                    "0$",
                    "bx %",
                    "#5",
                    "1!",
                    "1\"",
                    "b01 %",
                    "#10",
                    "0!",
                    "1#",
                    "b10 %",
                ]),
                encoding="utf-8",
            )
            return 1, raw

        with patch.object(srv, "_run_harness_service", side_effect=fake_harness_service):
            r = await srv.tool_verify_feedback(_req(), VerifyFeedbackRequest(reason="after passing compile"))

        payload = json.loads(r.output)["verifier_feedback"]
        rendered = json.dumps(payload)
        wave = payload["waveform_observations"]
        rendered_wave = json.dumps(wave).lower()
        assert payload["partial_score"] == 0.2
        assert payload["tests_passed"] == 1
        assert payload["tests_total"] == 5
        assert "expected 0, got 1" in payload["first_failure"]
        assert payload["failed_test_names"] == ["test_output_mismatch"]
        assert wave["available"] is True
        assert wave["files_analyzed"] == 1
        assert wave["unknown_or_high_impedance_count"] == 1
        assert "state" in wave["signals_with_unknowns"]
        assert "expected_value" not in rendered_wave
        assert "dump.vcd" not in rendered
        assert "/src/test_runner.py" not in rendered
        assert "docker-compose" not in rendered
        assert "harness" not in rendered.lower()
        assert not (sb / "docker-compose.yml").exists()
        assert not (sb / "src" / "test_runner.py").exists()

        r = await srv.tool_verify_feedback(_req(), VerifyFeedbackRequest(reason="try again"))
        assert json.loads(r.output)["error"] == "verify_feedback_budget_exhausted"

    def test_compile_phase_not_false_timeout_from_traceback_boilerplate(self):
        raw = (
            "CalledProcessError: Command '['iverilog'] returned non-zero exit status 1.\n"
            "If timeout is given, and the process takes too long, a TimeoutExpired exception will be raised.\n"
            "FAILED ../../src/test_runner.py::test_compile_case[0]\n"
        )
        payload = CVDPAgenticHeavyResourcesServer._build_verify_feedback(
            exit_code=1,
            stderr=raw,
            service_results=[{"service": "direct", "exit_code": 1, "stderr": raw}],
            private_root=None,
        )
        assert payload["failure_phase"] == "compile"
        assert payload["timeout"] is False
        assert payload["failed_test_names"] == ["test_compile_case"]
        rendered = json.dumps(payload).lower()
        assert "test_runner" not in rendered
        assert "/src" not in rendered


# ---------------------------------------------------------------------------
# Tests: SessionState cleanup
# ---------------------------------------------------------------------------


class TestSessionState:
    @pytest.mark.asyncio
    async def test_cleanup_removes_sandbox(self):
        sb = Path(tempfile.mkdtemp())
        (sb / "t.txt").write_text("x")
        session = SessionState(sandbox=sb, container_id="")
        await session.cleanup()
        assert not sb.exists()
