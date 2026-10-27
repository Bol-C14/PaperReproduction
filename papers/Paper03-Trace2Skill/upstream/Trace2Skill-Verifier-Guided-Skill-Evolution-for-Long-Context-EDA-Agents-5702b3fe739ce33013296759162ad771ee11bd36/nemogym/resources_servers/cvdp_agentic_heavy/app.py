# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import difflib
import fnmatch
import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from nemo_gym.base_resources_server import (
    BaseResourcesServerConfig,
    BaseRunRequest,
    BaseSeedSessionRequest,
    BaseSeedSessionResponse,
    BaseVerifyRequest,
    BaseVerifyResponse,
    SimpleResourcesServer,
)
from nemo_gym.server_utils import SESSION_ID_KEY

try:
    from resources_servers.cvdp_agentic_heavy.context_pruning import CONTEXT_PRUNING_META_KEY
except ImportError:  # pragma: no cover - app.py is also executed directly by ng_run
    from context_pruning import CONTEXT_PRUNING_META_KEY


# ----------------------------
# Config
# ----------------------------

DEFAULT_CVDP_OSS_IMAGE = os.environ.get(
    "CVDP_OSS_SIM_IMAGE",
    "trace2skill/cvdp-sim-cocotb-compat:latest",
)


class CVDPAgenticHeavyConfig(BaseResourcesServerConfig):
    oss_sim_image: str = DEFAULT_CVDP_OSS_IMAGE
    oss_pnr_image: str = os.environ.get("CVDP_OSS_PNR_IMAGE", DEFAULT_CVDP_OSS_IMAGE)
    eda_sim_image: str = ""
    license_network_name: str = ""
    docker_timeout: int = 600
    tool_timeout: int = 120
    num_processes: int = 4
    docker_root_min_free_gb: int = Field(
        default_factory=lambda: _int_env("CVDP_DOCKER_ROOT_MIN_FREE_GB", 20)
    )
    docker_root_min_free_inodes: int = Field(
        default_factory=lambda: _int_env("CVDP_DOCKER_ROOT_MIN_FREE_INODES", 10_000)
    )
    cleanup_stale_containers_on_start: bool = os.environ.get(
        "CVDP_CLEAN_STALE_CONTAINERS_ON_START", "0"
    ).strip().lower() not in {"0", "false", "no"}
    stale_container_max_age_seconds: int = Field(
        default_factory=lambda: _int_env("CVDP_STALE_CONTAINER_MAX_AGE_SECONDS", 8 * 3600)
    )
    # Opus long-context rollouts can legitimately run for more than an hour.
    # The session is still cleaned immediately after verify; this only controls
    # emergency cleanup for abandoned sessions.
    session_max_age_seconds: int = 28800
    runtime_verifier_feedback_enabled: bool = Field(
        default_factory=lambda: os.environ.get(
            "CVDP_RUNTIME_VERIFIER_FEEDBACK_ENABLED", "0"
        ).strip().lower() in {"1", "true", "yes", "on"}
    )
    runtime_verifier_feedback_max_calls: int = Field(
        default_factory=lambda: _int_env("CVDP_RUNTIME_VERIFIER_FEEDBACK_MAX_CALLS", 3)
    )
    runtime_verifier_feedback_artifact_root: str = Field(
        default_factory=lambda: os.environ.get(
            "CVDP_RUNTIME_VERIFIER_FEEDBACK_ARTIFACT_ROOT",
            str(Path(tempfile.gettempdir()) / "trace2skill_runtime_verifier_feedback"),
        )
    )


# ----------------------------
# Schemas
# ----------------------------


class CVDPAgenticHeavyVerifierMetadata(BaseModel):
    task_id: str
    categories: List[str] = []
    difficulty: str = ""
    context_files: Dict[str, str]
    harness_files: Dict[str, Optional[str]]
    patch: Optional[Dict[str, str]] = None
    origin: Optional[Dict[str, str]] = None


class AgenticHeavySeedRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    verifier_metadata: Optional[Dict[str, Any]] = None


class CVDPAgenticHeavyVerifyRequest(BaseVerifyRequest):
    verifier_metadata: Dict[str, Any]


class CVDPAgenticHeavyVerifyResponse(BaseVerifyResponse):
    task_id: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    docker_exit_code: Optional[int] = None
    docker_stderr: Optional[str] = None
    docker_services: Optional[List[Dict]] = None
    execution_time: Optional[float] = None
    tests_passed: Optional[int] = None
    tests_total: Optional[int] = None


# ----------------------------
# Docker harness helpers
# ----------------------------


def _apply_substitutions(content: str, config: CVDPAgenticHeavyConfig) -> str:
    substitutions = {
        "__VERIF_EDA_IMAGE__": config.eda_sim_image,
        "__LICENSE_NETWORK__": config.license_network_name,
        "__OSS_SIM_IMAGE__": config.oss_sim_image,
        "__OSS_PNR_IMAGE__": config.oss_pnr_image,
    }
    for placeholder, value in substitutions.items():
        if value and placeholder in content:
            content = content.replace(placeholder, value)
    return content


def _filter_code_volumes(compose_content: str) -> str:
    data = yaml.safe_load(compose_content)
    if not data or "services" not in data:
        return compose_content
    for service_name, service_config in data["services"].items():
        if "volumes" in service_config:
            filtered = [vol for vol in service_config["volumes"] if "/code" not in vol]
            service_config["volumes"] = filtered
    return yaml.dump(data, default_flow_style=False)


# ----------------------------
# Per-session state
# ----------------------------


class SessionState:
    """Tracks the sandbox directory and long-running Docker container for one rollout."""

    def __init__(
        self,
        sandbox: Path,
        container_id: str,
        restore_store_path: Optional[Path] = None,
        original_files: Optional[Dict[str, str]] = None,
        verifier_metadata: Optional[Dict[str, Any]] = None,
        feedback_artifact_dir: Optional[Path] = None,
    ):
        self.sandbox = sandbox
        self.container_id = container_id
        self.restore_store_path = restore_store_path
        self.original_files = dict(original_files or {})
        self.verifier_metadata = dict(verifier_metadata or {})
        self.feedback_artifact_dir = feedback_artifact_dir
        self.write_count = 0
        self.last_successful_compile_write_count: Optional[int] = None
        self.verifier_feedback_calls = 0
        self.write_count_at_last_feedback: Optional[int] = None
        self.verifier_feedback_policy_violations = 0
        self.verifier_feedback_events: list[dict[str, Any]] = []
        self.created_at = time.time()

    async def cleanup(self) -> None:
        if self.container_id:
            for cmd in [
                ["docker", "kill", self.container_id],
                ["docker", "rm", "-f", self.container_id],
            ]:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
                    )
                    await asyncio.wait_for(proc.wait(), timeout=15)
                except Exception:
                    pass
        if self.sandbox.exists():
            shutil.rmtree(self.sandbox, ignore_errors=True)


# ----------------------------
# Server
# ----------------------------


class ToolRequest(BaseModel):
    model_config = ConfigDict(extra="allow")


class ToolResponse(BaseModel):
    output: str


class VerifyFeedbackRequest(ToolRequest):
    reason: str = ""


MAX_OUTPUT_CHARS = 50_000
TRACE_SKILL_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CVDP_TMPDIR = Path(tempfile.gettempdir())
DEFAULT_MIN_FREE_GB = 20
DEFAULT_MIN_FREE_INODES = 10_000
MAX_DIAGNOSTIC_MATCHES = 200
MAX_DIAGNOSTIC_FILE_BYTES = 2_000_000
MAX_VERIFY_FEEDBACK_CHARS = 600
MAX_WAVEFORM_FILES = 3
MAX_WAVEFORM_BYTES = 5_000_000
RTL_SUFFIXES = {".v", ".sv", ".vh", ".svh"}
SENSITIVE_VERIFY_MARKERS = (
    "test_runner.py",
    "harness.py",
    "docker-compose",
    "reference solution",
    "solution.py",
    "golden",
)
SENSITIVE_WAVEFORM_NAME_TOKENS = (
    "tb",
    "test",
    "harness",
    "checker",
    "scoreboard",
    "score",
    "expected",
    "golden",
    "reference",
    "solution",
    "cocotb",
    "pytest",
)
try:
    MAX_WRITE_BYTES = int(os.environ.get("CVDP_MAX_WRITE_BYTES", "50000000"))
except ValueError:
    MAX_WRITE_BYTES = 50_000_000


def _sanitize_docker_name(name: str) -> str:
    """Docker project/container names must be [a-z0-9_-] and start with [a-z0-9]."""
    import re
    name = re.sub(r"[^a-z0-9_-]", "_", name.lower())
    name = re.sub(r"^[^a-z0-9]+", "", name)
    return name or "cvdp"


def _resolve_restore_store_path(raw_store_path: str) -> Path:
    """Resolve pruned-context sidecar stores from portable repo-relative paths."""
    candidate = Path(str(raw_store_path)).expanduser()
    if candidate.is_absolute():
        return candidate

    repo_relative = TRACE_SKILL_ROOT / candidate
    if repo_relative.exists():
        return repo_relative
    return candidate.resolve()


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _resolve_sandbox_root() -> Path:
    """Resolve the scratch root used for CVDP rollout sandboxes.

    Prefer the explicit CVDP_TMPDIR, then TMPDIR, then the platform temporary
    directory. The public launcher sets CVDP_TMPDIR inside the repository's
    ignored runs tree unless the user selects a larger scratch volume.
    """
    raw = os.environ.get("CVDP_TMPDIR") or os.environ.get("TMPDIR")
    if raw:
        return Path(raw).expanduser()
    return DEFAULT_CVDP_TMPDIR


def _scratch_health(path: Path) -> dict:
    usage = shutil.disk_usage(path)
    stat = os.statvfs(path)
    return {
        "path": str(path),
        "free_bytes": int(usage.free),
        "free_gb": usage.free / (1024 ** 3),
        "total_gb": usage.total / (1024 ** 3),
        "free_inodes": int(stat.f_favail),
    }


def _require_scratch_capacity(path: Path, *, task_id: str, context_files: Dict[str, str] | None = None) -> dict:
    """Fail fast when sandbox scratch capacity is below safety thresholds."""
    path.mkdir(parents=True, exist_ok=True)
    health = _scratch_health(path)
    min_free_gb = _int_env("CVDP_TMPDIR_MIN_FREE_GB", DEFAULT_MIN_FREE_GB)
    min_free_inodes = _int_env("CVDP_TMPDIR_MIN_FREE_INODES", DEFAULT_MIN_FREE_INODES)
    context_bytes = sum(len(str(content).encode("utf-8")) for content in (context_files or {}).values())
    required_bytes = (min_free_gb * 1024 ** 3) + (3 * context_bytes)
    if health["free_bytes"] < required_bytes or health["free_inodes"] < min_free_inodes:
        raise RuntimeError(
            "CVDP scratch space is below safety threshold before seed_session "
            f"for task {task_id}: path={health['path']}, free={health['free_gb']:.1f} GiB, "
            f"free_inodes={health['free_inodes']}, required_free_gb>={min_free_gb}, "
            f"required_free_inodes>={min_free_inodes}, context_payload={context_bytes} bytes. "
            "Set CVDP_TMPDIR to a larger scratch volume or clean stale artifacts before launching."
        )
    return health


class CVDPAgenticHeavyResourcesServer(SimpleResourcesServer):
    config: CVDPAgenticHeavyConfig
    _sessions: Dict[str, SessionState] = {}

    def model_post_init(self, context: Any) -> None:
        self._semaphore = asyncio.Semaphore(value=self.config.num_processes)
        self._sessions = {}

    def setup_webserver(self) -> FastAPI:
        app = super().setup_webserver()
        app.post("/ls")(self.tool_ls)
        app.post("/cat")(self.tool_cat)
        app.post("/rg")(self.tool_rg)
        app.post("/find_files")(self.tool_find_files)
        app.post("/read_file")(self.tool_read_file)
        app.post("/show_changes")(self.tool_show_changes)
        app.post("/module_index")(self.tool_module_index)
        app.post("/echo")(self.tool_echo)
        app.post("/edit")(self.tool_edit)
        app.post("/restore_file")(self.tool_restore_file)
        app.post("/iverilog")(self.tool_iverilog)
        app.post("/vvp")(self.tool_vvp)
        app.post("/xcelium")(self.tool_xcelium)
        app.post("/verify_feedback")(self.tool_verify_feedback)
        app.post("/pwd")(self.tool_pwd)
        app.post("/cleanup_session")(self.cleanup_session)

        @app.on_event("startup")
        async def start_reaper():
            if self.config.cleanup_stale_containers_on_start:
                await self._cleanup_stale_harness_containers(reason="startup")
            await self._require_docker_root_capacity(task_id="startup")
            asyncio.create_task(self._reap_stale_sessions())

        @app.on_event("shutdown")
        async def cleanup_live_sessions():
            await self._cleanup_all_sessions(reason="shutdown")

        return app

    async def _run_docker_command(self, *args: str, timeout: int = 30) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return (
            proc.returncode,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )

    async def _docker_root_health(self) -> dict:
        rc, stdout, stderr = await self._run_docker_command(
            "info", "--format", "{{.DockerRootDir}}", timeout=20
        )
        if rc != 0:
            raise RuntimeError(f"docker info failed while checking Docker root: {stderr[:500]}")
        root = Path(stdout.strip() or "/var/lib/docker")
        usage = shutil.disk_usage(root)
        stat = os.statvfs(root)
        return {
            "path": str(root),
            "free_bytes": int(usage.free),
            "free_gb": usage.free / (1024 ** 3),
            "total_gb": usage.total / (1024 ** 3),
            "free_inodes": int(stat.f_favail),
        }

    def _active_session_container_ids(self) -> set[str]:
        return {session.container_id for session in self._sessions.values() if session.container_id}

    async def _cleanup_stale_harness_containers(self, *, reason: str) -> int:
        """Remove old CVDP rollout containers left behind by interrupted servers.

        Normal rollouts clean up after verify. If ng_run is killed before verify
        or before the in-memory session map can run cleanup, Docker containers
        named cvdp_ah_* can remain alive and consume /var/lib/docker overlay
        space. This reaper is intentionally scoped to our harness container name.
        """
        rc, stdout, stderr = await self._run_docker_command(
            "ps",
            "-a",
            "--filter",
            "name=cvdp_ah_",
            "--format",
            "{{.ID}}\t{{.Names}}\t{{.Status}}",
            timeout=30,
        )
        if rc != 0:
            print(f"[docker-cleanup] docker ps failed during {reason}: {stderr[:500]}")
            return 0

        now = int(time.time())
        max_age = max(0, int(self.config.stale_container_max_age_seconds or 0))
        active_ids = self._active_session_container_ids()
        remove_ids: list[str] = []

        for line in stdout.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            cid, name, status = parts
            if cid in active_ids:
                continue
            suffix = re.search(r"_(\d{10})$", name)
            age = now - int(suffix.group(1)) if suffix else None
            status_l = status.lower()
            if status_l.startswith(("exited", "created", "dead")):
                remove_ids.append(cid)
            elif age is not None and age > max_age:
                remove_ids.append(cid)

        if not remove_ids:
            return 0

        print(
            f"[docker-cleanup] Removing {len(remove_ids)} stale cvdp_ah container(s) "
            f"during {reason}; max_age={max_age}s"
        )
        removed = 0
        for cid in remove_ids:
            rc, _, stderr = await self._run_docker_command("rm", "-f", cid, timeout=30)
            if rc == 0:
                removed += 1
            else:
                print(f"[docker-cleanup] failed to remove {cid}: {stderr[:300]}")
        return removed

    async def _require_docker_root_capacity(self, *, task_id: str) -> dict:
        health = await self._docker_root_health()
        min_free_gb = max(0, int(self.config.docker_root_min_free_gb or 0))
        min_free_inodes = max(0, int(self.config.docker_root_min_free_inodes or 0))
        min_free_bytes = min_free_gb * 1024 ** 3

        if (
            self.config.cleanup_stale_containers_on_start
            and (health["free_bytes"] < min_free_bytes or health["free_inodes"] < min_free_inodes)
        ):
            await self._cleanup_stale_harness_containers(reason=f"low_docker_space:{task_id}")
            health = await self._docker_root_health()

        if health["free_bytes"] < min_free_bytes or health["free_inodes"] < min_free_inodes:
            raise RuntimeError(
                "Docker root storage is below safety threshold before seed_session "
                f"for task {task_id}: path={health['path']}, free={health['free_gb']:.1f} GiB, "
                f"free_inodes={health['free_inodes']}, required_free_gb>={min_free_gb}, "
                f"required_free_inodes>={min_free_inodes}. "
                "Clean stale Docker containers/volumes or move DockerRootDir to a larger volume."
            )
        return health

    async def _cleanup_all_sessions(self, *, reason: str) -> None:
        sessions = list(self._sessions.items())
        self._sessions.clear()
        if sessions:
            print(f"[cleanup] Cleaning {len(sessions)} live CVDP session(s) during {reason}")
        for _, session in sessions:
            await session.cleanup()

    async def _reap_stale_sessions(self, max_age: int = 3600) -> None:
        """Periodically clean up sessions older than max_age seconds."""
        while True:
            await asyncio.sleep(120)
            now = time.time()
            effective_max_age = self.config.session_max_age_seconds or max_age
            stale = [sid for sid, s in self._sessions.items() if now - s.created_at > effective_max_age]
            for sid in stale:
                session = self._sessions.pop(sid, None)
                if session:
                    print(f"[reaper] Cleaning stale session {sid[:8]} (age {now - session.created_at:.0f}s)")
                    await session.cleanup()

    async def cleanup_session(self, request: Request) -> dict:
        """Explicitly clean up a session's Docker container and sandbox."""
        session_id = request.session.get(SESSION_ID_KEY, "")
        session = self._sessions.pop(session_id, None)
        if session:
            await session.cleanup()
            return {"status": "cleaned", "session_id": session_id[:8]}
        return {"status": "no_session"}

    def _get_session(self, request: Request) -> SessionState:
        session_id = request.session.get(SESSION_ID_KEY, "")
        session = self._sessions.get(session_id)
        if session is None:
            raise HTTPException(status_code=400, detail="No session found. Call seed_session first.")
        return session

    async def _docker_exec(self, session: SessionState, cmd: str, timeout: int) -> str:
        """Execute a command inside the session's long-running Docker container."""
        exec_cmd = ["docker", "exec", session.container_id, "sh", "-c", cmd]
        try:
            proc = await asyncio.create_subprocess_exec(
                *exec_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            output = (stdout + stderr).decode("utf-8", errors="replace")
            if len(output) > MAX_OUTPUT_CHARS:
                output = output[:MAX_OUTPUT_CHARS] + "\n... (truncated)"
            exit_info = f"[exit code: {proc.returncode}]"
            return f"{output}\n{exit_info}" if output.strip() else exit_info
        except asyncio.TimeoutError:
            return f"Error: command timed out after {timeout}s"

    # ------ Session management ------

    async def seed_session(self, request: Request, body: AgenticHeavySeedRequest) -> BaseSeedSessionResponse:
        """Set up a per-rollout sandbox and start a long-running Docker container."""
        session_id = request.session[SESSION_ID_KEY]
        meta = body.verifier_metadata or {}
        context_files = meta.get("context_files", {})
        task_id = meta.get("task_id", "unknown")
        restore_store_path: Optional[Path] = None
        pruning_meta = meta.get(CONTEXT_PRUNING_META_KEY) or {}
        if isinstance(pruning_meta, dict) and pruning_meta.get("enabled"):
            raw_store_path = pruning_meta.get("store_path")
            if raw_store_path:
                restore_store_path = _resolve_restore_store_path(str(raw_store_path))

        # Clean up any previous session
        if session_id in self._sessions:
            await self._sessions[session_id].cleanup()

        sandbox_root = _resolve_sandbox_root()
        scratch_health = _require_scratch_capacity(sandbox_root, task_id=task_id, context_files=context_files)
        docker_health = await self._require_docker_root_capacity(task_id=task_id)
        print(
            f"[seed_session] scratch={scratch_health['path']} "
            f"free={scratch_health['free_gb']:.1f}GiB inodes={scratch_health['free_inodes']} "
            f"docker_root={docker_health['path']} docker_free={docker_health['free_gb']:.1f}GiB"
        )
        sandbox = Path(tempfile.mkdtemp(prefix=f"cvdp_agentic_{task_id}_", dir=str(sandbox_root)))

        try:
            for filepath, content in context_files.items():
                dest = sandbox / filepath
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")

            # Create standard dirs expected by the harness
            for d in ["rundir", "verif", "docs"]:
                (sandbox / d).mkdir(exist_ok=True)
        except Exception:
            shutil.rmtree(sandbox, ignore_errors=True)
            raise

        # Start a long-running Docker container with the sandbox mounted as /code.
        # The container stays alive for the entire episode so tool calls use `docker exec`.
        container_name = _sanitize_docker_name(f"cvdp_ah_{task_id}_{session_id[:8]}_{int(time.time())}")
        uid = os.getuid()
        gid = os.getgid()

        start_cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--label", "cvdp.agentic_heavy=1",
            "--label", f"cvdp.task_id={task_id}",
            "--label", f"cvdp.session_id={session_id}",
            "--user", f"{uid}:{gid}",
            "-v", f"{sandbox}:/code",
            "-w", "/code",
            "-e", "HOME=/code/rundir",
        ]
        docker_memory_limit = os.environ.get("CVDP_DOCKER_MEMORY_LIMIT", "").strip()
        if docker_memory_limit:
            start_cmd.extend(["--memory", docker_memory_limit])
        start_cmd.extend([
            self.config.oss_sim_image,
            "sleep", "infinity",
        ])

        proc = await asyncio.create_subprocess_exec(
            *start_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="replace")
            print(f"[seed_session] Docker container start FAILED for {task_id}: exit={proc.returncode} err={err[:500]}")
            shutil.rmtree(sandbox, ignore_errors=True)
            raise RuntimeError(f"Failed to start Docker container for {task_id}: {err[:500]}")

        container_id = stdout.decode().strip()
        feedback_artifact_dir: Optional[Path] = None
        if self.config.runtime_verifier_feedback_enabled:
            artifact_root = Path(self.config.runtime_verifier_feedback_artifact_root).expanduser()
            feedback_artifact_dir = (
                artifact_root
                / _sanitize_docker_name(str(task_id))
                / _sanitize_docker_name(session_id[:12])
            )
            feedback_artifact_dir.mkdir(parents=True, exist_ok=True)

        self._sessions[session_id] = SessionState(
            sandbox=sandbox,
            container_id=container_id,
            restore_store_path=restore_store_path,
            original_files=context_files,
            verifier_metadata=meta,
            feedback_artifact_dir=feedback_artifact_dir,
        )

        return BaseSeedSessionResponse(**body.model_dump())

    # ------ Filesystem tools (direct host operations on sandbox) ------

    @staticmethod
    def _normalize_path(user_path: str) -> str:
        """Strip /code/ prefix so absolute Docker paths become sandbox-relative."""
        if user_path.startswith("/code/"):
            return user_path[len("/code/"):]
        if user_path == "/code":
            return "."
        if user_path.startswith("/"):
            return user_path.lstrip("/")
        return user_path

    @staticmethod
    def _path_in_sandbox(session: SessionState, user_path: str) -> tuple[Optional[Path], Optional[str]]:
        normalized = CVDPAgenticHeavyResourcesServer._normalize_path(user_path or ".")
        try:
            root = session.sandbox.resolve()
            target = (session.sandbox / normalized).resolve()
            target.relative_to(root)
            return target, None
        except Exception:
            return None, f"Error: path escapes sandbox: {user_path}"

    @staticmethod
    def _relpath(session: SessionState, target: Path) -> str:
        try:
            return target.resolve().relative_to(session.sandbox.resolve()).as_posix()
        except Exception:
            return target.as_posix()

    @staticmethod
    def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
        if len(text) <= limit:
            return text
        return text[:limit] + f"\n... (truncated, {len(text)} chars total)"

    @staticmethod
    def _iter_files(root: Path) -> List[Path]:
        if root.is_file():
            return [root]
        files: List[Path] = []
        for current_root, dirs, filenames in os.walk(root):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]
            for name in filenames:
                files.append(Path(current_root) / name)
        return sorted(files)

    @staticmethod
    def _read_small_text(path: Path) -> Optional[str]:
        try:
            if path.stat().st_size > MAX_DIAGNOSTIC_FILE_BYTES:
                return None
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

    @staticmethod
    def _mark_write(session: SessionState) -> None:
        session.write_count += 1
        # A compile result is only meaningful for the code version it checked.
        session.last_successful_compile_write_count = None

    @staticmethod
    def _bounded_int(value: Any, default: int, low: int, high: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return min(max(parsed, low), high)

    async def tool_ls(self, request: Request, body: ToolRequest) -> ToolResponse:
        session = self._get_session(request)
        user_path = self._normalize_path(body.model_dump().get("path", "."))
        try:
            target = (session.sandbox / user_path).resolve()
            if not str(target).startswith(str(session.sandbox.resolve())):
                return ToolResponse(output=f"Error: path escapes sandbox: {user_path}")
            if not target.exists():
                return ToolResponse(output=f"Error: no such directory: {user_path}")
            if not target.is_dir():
                return ToolResponse(output=f"Error: not a directory: {user_path}")
            entries = sorted(os.listdir(target))
            return ToolResponse(output="\n".join(entries))
        except Exception as e:
            return ToolResponse(output=f"Error: {e}")

    async def tool_cat(self, request: Request, body: ToolRequest) -> ToolResponse:
        session = self._get_session(request)
        filename = self._normalize_path(body.model_dump().get("filename", ""))
        if not filename:
            return ToolResponse(output="Error: filename is required")
        try:
            target = (session.sandbox / filename).resolve()
            if not str(target).startswith(str(session.sandbox.resolve())):
                return ToolResponse(output=f"Error: path escapes sandbox: {filename}")
            if not target.exists():
                return ToolResponse(output=f"Error: file not found: {filename}")
            if not target.is_file():
                return ToolResponse(output=f"Error: not a file: {filename}")
            content = target.read_text(encoding="utf-8", errors="replace")
            if len(content) > MAX_OUTPUT_CHARS:
                content = content[:MAX_OUTPUT_CHARS] + f"\n... (truncated, {len(content)} chars total)"
            return ToolResponse(output=content)
        except Exception as e:
            return ToolResponse(output=f"Error: {e}")

    async def tool_rg(self, request: Request, body: ToolRequest) -> ToolResponse:
        """Search visible sandbox files for a regex pattern, similar to ripgrep."""
        session = self._get_session(request)
        data = body.model_dump()
        pattern = str(data.get("pattern", ""))
        if not pattern:
            return ToolResponse(output="Error: pattern is required")
        path = str(data.get("path", ".") or ".")
        glob = str(data.get("glob", "*") or "*")
        case_sensitive = bool(data.get("case_sensitive", False))
        max_matches = self._bounded_int(data.get("max_matches"), MAX_DIAGNOSTIC_MATCHES, 1, 1000)
        target, error = self._path_in_sandbox(session, path)
        if error:
            return ToolResponse(output=error)
        assert target is not None
        if not target.exists():
            return ToolResponse(output=f"Error: path not found: {path}")
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            rx = re.compile(pattern, flags)
        except re.error as exc:
            return ToolResponse(output=f"Error: invalid regex: {exc}")

        matches: List[str] = []
        for file_path in self._iter_files(target):
            rel = self._relpath(session, file_path)
            if not fnmatch.fnmatch(rel, glob) and not fnmatch.fnmatch(file_path.name, glob):
                continue
            text = self._read_small_text(file_path)
            if text is None:
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    if len(line) > 300:
                        line = line[:300] + " ..."
                    matches.append(f"{rel}:{line_no}: {line}")
                    if len(matches) >= max_matches:
                        output = "\n".join(matches) + f"\n... ({max_matches} match limit reached)"
                        return ToolResponse(output=self._truncate(output))
        return ToolResponse(output="\n".join(matches) if matches else "No matches")

    async def tool_find_files(self, request: Request, body: ToolRequest) -> ToolResponse:
        """Find files by glob under a visible sandbox path."""
        session = self._get_session(request)
        data = body.model_dump()
        path = str(data.get("path", ".") or ".")
        glob = str(data.get("glob", "*") or "*")
        max_results = self._bounded_int(data.get("max_results"), 300, 1, 2000)
        target, error = self._path_in_sandbox(session, path)
        if error:
            return ToolResponse(output=error)
        assert target is not None
        if not target.exists():
            return ToolResponse(output=f"Error: path not found: {path}")

        files: List[str] = []
        for file_path in self._iter_files(target):
            rel = self._relpath(session, file_path)
            if fnmatch.fnmatch(rel, glob) or fnmatch.fnmatch(file_path.name, glob):
                files.append(rel)
                if len(files) >= max_results:
                    return ToolResponse(output="\n".join(files) + f"\n... ({max_results} result limit reached)")
        return ToolResponse(output="\n".join(files) if files else "No files matched")

    async def tool_read_file(self, request: Request, body: ToolRequest) -> ToolResponse:
        """Read a line range from a visible sandbox file with line numbers."""
        session = self._get_session(request)
        data = body.model_dump()
        filename = str(data.get("filename", ""))
        if not filename:
            return ToolResponse(output="Error: filename is required")
        start_line = self._bounded_int(data.get("start_line"), 1, 1, 10_000_000)
        end_line_raw = data.get("end_line")
        end_line = self._bounded_int(end_line_raw, start_line + 199, 1, 10_000_000)
        if end_line < start_line:
            return ToolResponse(output="Error: end_line must be >= start_line")
        if end_line - start_line > 500:
            end_line = start_line + 500
        target, error = self._path_in_sandbox(session, filename)
        if error:
            return ToolResponse(output=error)
        assert target is not None
        if not target.exists() or not target.is_file():
            return ToolResponse(output=f"Error: file not found: {filename}")
        text = self._read_small_text(target)
        if text is None:
            return ToolResponse(output=f"Error: file is too large or unreadable: {filename}")

        lines = text.splitlines()
        selected = lines[start_line - 1:end_line]
        if not selected:
            return ToolResponse(output=f"{filename}: no lines in requested range {start_line}-{end_line}")
        width = len(str(start_line + len(selected) - 1))
        rendered = [f"{idx:>{width}} | {line}" for idx, line in enumerate(selected, start_line)]
        output = f"{filename}:{start_line}-{start_line + len(selected) - 1}\n" + "\n".join(rendered)
        return ToolResponse(output=self._truncate(output))

    async def tool_show_changes(self, request: Request, body: ToolRequest) -> ToolResponse:
        """Show unified diffs between current sandbox files and original visible context."""
        session = self._get_session(request)
        data = body.model_dump()
        requested = data.get("filename")
        max_files = self._bounded_int(data.get("max_files"), 40, 1, 200)
        original_files = session.original_files

        current_files: Dict[str, str] = {}
        if requested:
            rel = self._normalize_path(str(requested))
            target, error = self._path_in_sandbox(session, rel)
            if error:
                return ToolResponse(output=error)
            assert target is not None
            if target.exists() and target.is_file():
                current_files[rel] = target.read_text(encoding="utf-8", errors="replace")
            keys = [rel]
        else:
            for file_path in self._iter_files(session.sandbox):
                rel = self._relpath(session, file_path)
                text = self._read_small_text(file_path)
                if text is not None:
                    current_files[rel] = text
            keys = sorted(set(original_files) | set(current_files))

        chunks: List[str] = []
        changed = 0
        for rel in keys:
            before = original_files.get(rel)
            after = current_files.get(rel)
            if before == after:
                continue
            changed += 1
            if changed > max_files:
                chunks.append(f"... ({max_files} changed-file limit reached)")
                break
            before_lines = [] if before is None else before.splitlines(keepends=True)
            after_lines = [] if after is None else after.splitlines(keepends=True)
            chunks.extend(
                difflib.unified_diff(
                    before_lines,
                    after_lines,
                    fromfile=f"original/{rel}",
                    tofile=f"current/{rel}",
                    lineterm="",
                    n=3,
                )
            )
        if not chunks:
            return ToolResponse(output="No changes from original visible context")
        return ToolResponse(output=self._truncate("\n".join(chunks)))

    async def tool_module_index(self, request: Request, body: ToolRequest) -> ToolResponse:
        """Summarize Verilog/SystemVerilog module declarations from visible files."""
        session = self._get_session(request)
        path = str(body.model_dump().get("path", ".") or ".")
        target, error = self._path_in_sandbox(session, path)
        if error:
            return ToolResponse(output=error)
        assert target is not None
        if not target.exists():
            return ToolResponse(output=f"Error: path not found: {path}")

        module_re = re.compile(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\b(?P<header>.*?);", re.DOTALL)
        line_comment_re = re.compile(r"//.*?$", re.MULTILINE)
        block_comment_re = re.compile(r"/\*.*?\*/", re.DOTALL)
        rows: List[str] = []
        for file_path in self._iter_files(target):
            if file_path.suffix not in RTL_SUFFIXES:
                continue
            text = self._read_small_text(file_path)
            if text is None:
                continue
            cleaned = block_comment_re.sub("", line_comment_re.sub("", text))
            rel = self._relpath(session, file_path)
            for match in module_re.finditer(cleaned):
                name = match.group(1)
                line_no = cleaned[:match.start()].count("\n") + 1
                declaration = " ".join(match.group(0).split())
                if len(declaration) > 500:
                    declaration = declaration[:500] + " ..."
                rows.append(f"{rel}:{line_no}: module {name}\n  declaration: {declaration}")
                if len(rows) >= 200:
                    rows.append("... (200 module limit reached)")
                    return ToolResponse(output=self._truncate("\n".join(rows)))
        return ToolResponse(output="\n".join(rows) if rows else "No Verilog modules found")

    async def tool_echo(self, request: Request, body: ToolRequest) -> ToolResponse:
        session = self._get_session(request)
        data = body.model_dump()
        content = data.get("content", "")
        filename = self._normalize_path(data.get("filename", ""))
        if not filename:
            return ToolResponse(output="Error: filename is required")
        content_bytes = len(content.encode("utf-8"))
        if content_bytes > MAX_WRITE_BYTES:
            return ToolResponse(output=f"Error: write too large ({content_bytes} bytes); limit is {MAX_WRITE_BYTES} bytes")
        try:
            _require_scratch_capacity(session.sandbox.parent, task_id=session.sandbox.name)
            target = (session.sandbox / filename).resolve()
            if not str(target).startswith(str(session.sandbox.resolve())):
                return ToolResponse(output=f"Error: path escapes sandbox: {filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            self._mark_write(session)
            return ToolResponse(output=f"Written {content_bytes} bytes to {filename}")
        except Exception as e:
            return ToolResponse(output=f"Error: {e}")

    async def tool_edit(self, request: Request, body: ToolRequest) -> ToolResponse:
        session = self._get_session(request)
        data = body.model_dump()
        filename = self._normalize_path(data.get("filename", ""))
        old_text = data.get("old_text", "")
        new_text = data.get("new_text", "")
        if not filename:
            return ToolResponse(output="Error: filename is required")
        if old_text == "":
            return ToolResponse(output="Error: old_text is required")
        try:
            target = (session.sandbox / filename).resolve()
            if not str(target).startswith(str(session.sandbox.resolve())):
                return ToolResponse(output=f"Error: path escapes sandbox: {filename}")
            if not target.exists():
                return ToolResponse(output=f"Error: file not found: {filename}")
            if not target.is_file():
                return ToolResponse(output=f"Error: not a file: {filename}")
            content = target.read_text(encoding="utf-8", errors="replace")
            count = content.count(old_text)
            if count == 0:
                return ToolResponse(output="Error: old_text not found")
            if count > 1:
                return ToolResponse(output=f"Error: old_text occurs {count} times; edit requires a unique match")
            updated = content.replace(old_text, new_text, 1)
            updated_bytes = len(updated.encode("utf-8"))
            if updated_bytes > MAX_WRITE_BYTES:
                return ToolResponse(output=f"Error: edited file too large ({updated_bytes} bytes); limit is {MAX_WRITE_BYTES} bytes")
            _require_scratch_capacity(session.sandbox.parent, task_id=session.sandbox.name)
            target.write_text(updated, encoding="utf-8")
            self._mark_write(session)
            return ToolResponse(
                output=f"Edited {filename}: replaced {len(old_text)} chars with {len(new_text)} chars"
            )
        except Exception as e:
            return ToolResponse(output=f"Error: {e}")

    async def tool_restore_file(self, request: Request, body: ToolRequest) -> ToolResponse:
        """Restore one exact file omitted by the recoverable context-pruning ablation."""
        session = self._get_session(request)
        filename = self._normalize_path(body.model_dump().get("filename", ""))
        if not filename:
            return ToolResponse(output="Error: filename is required")
        if session.restore_store_path is None:
            return ToolResponse(output="Error: no pruned context store is configured for this task")
        try:
            target = (session.sandbox / filename).resolve()
            if not str(target).startswith(str(session.sandbox.resolve())):
                return ToolResponse(output=f"Error: path escapes sandbox: {filename}")
            store_path = session.restore_store_path
            if not store_path.exists() or not store_path.is_file():
                return ToolResponse(output=f"Error: pruned context store not found: {store_path}")
            with store_path.open(encoding="utf-8") as f:
                store = json.load(f)
            files = store.get("files", {})
            if filename not in files:
                available = sorted(files)[:20]
                preview = ", ".join(available)
                suffix = "" if len(files) <= 20 else f", ... ({len(files) - 20} more)"
                return ToolResponse(
                    output=f"Error: file is not restorable: {filename}. Available examples: {preview}{suffix}"
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            content = files[filename]
            content_bytes = len(content.encode("utf-8", errors="replace"))
            if content_bytes > MAX_WRITE_BYTES:
                return ToolResponse(output=f"Error: restore file too large ({content_bytes} bytes); limit is {MAX_WRITE_BYTES} bytes")
            _require_scratch_capacity(session.sandbox.parent, task_id=session.sandbox.name)
            target.write_text(content, encoding="utf-8")
            return ToolResponse(output=f"Restored {filename} ({content_bytes} bytes)")
        except Exception as e:
            return ToolResponse(output=f"Error: {e}")

    async def tool_pwd(self, request: Request, body: ToolRequest) -> ToolResponse:
        return ToolResponse(output="/code")

    # ------ Simulation tools (execute via docker exec in session container) ------

    async def tool_iverilog(self, request: Request, body: ToolRequest) -> ToolResponse:
        session = self._get_session(request)
        args = body.model_dump().get("args", "")
        if not args:
            return ToolResponse(output="Error: args is required")
        result = await self._docker_exec(session, f"cd /code && iverilog {args}", timeout=self.config.tool_timeout)
        if "[exit code: 0]" in result:
            session.last_successful_compile_write_count = session.write_count
        return ToolResponse(output=result)

    async def tool_vvp(self, request: Request, body: ToolRequest) -> ToolResponse:
        session = self._get_session(request)
        filename = body.model_dump().get("filename", "")
        if not filename:
            return ToolResponse(output="Error: filename is required")
        result = await self._docker_exec(session, f"cd /code && vvp {filename}", timeout=self.config.tool_timeout)
        return ToolResponse(output=result)

    async def tool_xcelium(self, request: Request, body: ToolRequest) -> ToolResponse:
        """Run Cadence Xcelium (xrun) inside the container.
        Requires eda_sim_image to be configured with Xcelium installed.
        TODO: may need a separate container with the commercial image."""
        session = self._get_session(request)
        args = body.model_dump().get("args", "")
        if not args:
            return ToolResponse(output="Error: args is required")
        result = await self._docker_exec(session, f"cd /code && xrun {args}", timeout=self.config.tool_timeout * 2)
        return ToolResponse(output=result)

    # ------ Runtime dense verifier feedback ------

    @staticmethod
    def _sanitize_verify_text(text: str, *, private_root: Optional[Path] = None) -> str:
        """Return a short functional failure summary without hidden harness details."""
        if not text:
            return ""
        cleaned_lines: list[str] = []
        private_root_text = str(private_root) if private_root else ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            low = line.lower()
            if low.startswith("traceback ") or low.startswith("file "):
                continue
            if any(marker in low for marker in SENSITIVE_VERIFY_MARKERS):
                continue
            if private_root_text and private_root_text in line:
                line = line.replace(private_root_text, "<private_workspace>")
            line = re.sub(r"/(?:src|tmp|var|mnt|home|code)/[^\s:'\"]+", "<path>", line)
            line = re.sub(r"\b[A-Za-z]:\\[^\s:'\"]+", "<path>", line)
            line = re.sub(r"\s+", " ", line).strip()
            if line:
                cleaned_lines.append(line)
            if len(" ".join(cleaned_lines)) >= MAX_VERIFY_FEEDBACK_CHARS:
                break
        return CVDPAgenticHeavyResourcesServer._truncate(
            " ".join(cleaned_lines), MAX_VERIFY_FEEDBACK_CHARS
        )

    @staticmethod
    def _parse_test_counts(text: str, pass_reward: bool) -> tuple[int, int]:
        if pass_reward:
            return 1, 1
        candidates: list[tuple[int, int]] = []
        for m in re.finditer(r"TESTS\s*=\s*(\d+)\s+PASS\s*=\s*(\d+)\s+FAIL\s*=\s*(\d+)", text):
            total = int(m.group(1))
            passed = int(m.group(2))
            failed = int(m.group(3))
            denom = total if total > 0 else passed + failed
            if denom > 0:
                candidates.append((passed, denom))
        for line in text.splitlines():
            low = line.lower()
            if "passed" not in low and "failed" not in low and "error" not in low:
                continue
            passed = sum(int(x) for x in re.findall(r"(\d+)\s+passed", line, re.IGNORECASE))
            failed = sum(int(x) for x in re.findall(r"(\d+)\s+failed", line, re.IGNORECASE))
            errors = sum(int(x) for x in re.findall(r"(\d+)\s+errors?", line, re.IGNORECASE))
            total = passed + failed + errors
            if total > 0:
                candidates.append((passed, total))
        if not candidates:
            return 0, 0
        return max(candidates, key=lambda item: item[0] / max(item[1], 1))

    @staticmethod
    def _safe_failed_test_name(raw_name: str) -> str:
        """Return only a test-like leaf name, never hidden harness filenames/paths."""
        if not raw_name:
            return ""
        name = str(raw_name).split("::")[-1]
        name = Path(name).name
        name = re.sub(r"\[[^\]]+\]", "", name)
        name = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")
        low = name.lower()
        if not name or name.endswith("_py") or low in {"test_runner", "runner", "harness"}:
            return ""
        sensitive_name_tokens = (
            "harness", "runner", "reference", "solution", "golden",
            "scoreboard", "checker", "cocotb", "pytest",
        )
        if any(token in low for token in sensitive_name_tokens):
            return ""
        if any(marker in low for marker in SENSITIVE_VERIFY_MARKERS):
            return ""
        if len(name) > 64:
            name = name[:61] + "..."
        return name

    @staticmethod
    def _failed_test_names(text: str) -> list[str]:
        names: list[str] = []
        patterns = [
            r"\b(test_[A-Za-z0-9_]+)\b.*\b(?:FAIL|failed|error)\b",
            r"\b([A-Za-z0-9_]+_test)\b.*\b(?:FAIL|failed|error)\b",
            r"\bFAILED\b\s+([A-Za-z0-9_./:<>\[\]-]+)",
            r"([A-Za-z0-9_./:-]+::test_[A-Za-z0-9_\[\]-]+)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = CVDPAgenticHeavyResourcesServer._safe_failed_test_name(match.group(1))
                if name and name not in names:
                    names.append(name)
                if len(names) >= 5:
                    return names
        return names

    @staticmethod
    def _safe_waveform_signal_name(raw_name: str) -> str:
        """Expose at most a sanitized leaf signal name from a dumped waveform."""
        if not raw_name:
            return ""
        leaf = raw_name.split(".")[-1].strip()
        leaf = re.sub(r"\[[^\]]+\]", "", leaf)
        leaf = re.sub(r"[^A-Za-z0-9_$]+", "_", leaf).strip("_")
        low = leaf.lower()
        if not leaf or any(token in low for token in SENSITIVE_WAVEFORM_NAME_TOKENS):
            return ""
        if len(leaf) > 48:
            leaf = leaf[:45] + "..."
        return leaf

    @classmethod
    def _summarize_vcd_file(cls, vcd_path: Path) -> Optional[dict]:
        """Parse a small VCD into safe activity observations, never raw waveform text."""
        try:
            if vcd_path.stat().st_size > MAX_WAVEFORM_BYTES:
                return {"skipped_large": True}
        except OSError:
            return None

        timescale = ""
        scopes: list[str] = []
        variables: dict[str, dict[str, Any]] = {}
        changes: dict[str, int] = {}
        xz_hits: dict[str, int] = {}
        max_time: Optional[int] = None
        current_time = 0

        try:
            with vcd_path.open("r", encoding="utf-8", errors="replace") as f:
                in_defs = True
                for raw_line in f:
                    line = raw_line.strip()
                    if not line:
                        continue
                    if in_defs:
                        if line.startswith("$timescale"):
                            timescale = line.replace("$timescale", "").replace("$end", "").strip()
                        elif line.startswith("$scope"):
                            parts = line.split()
                            if len(parts) >= 3:
                                scopes.append(parts[2])
                        elif line.startswith("$upscope"):
                            if scopes:
                                scopes.pop()
                        elif line.startswith("$var"):
                            parts = line.split()
                            if len(parts) >= 5:
                                code = parts[3]
                                raw_ref = " ".join(parts[4:-1]) if parts[-1] == "$end" else parts[4]
                                hier = ".".join(scopes + [raw_ref])
                                safe = cls._safe_waveform_signal_name(hier)
                                if safe:
                                    variables[code] = {"name": safe, "hier": hier}
                        elif line.startswith("$enddefinitions"):
                            in_defs = False
                        continue

                    if line.startswith("#"):
                        try:
                            current_time = int(line[1:].strip())
                            max_time = current_time if max_time is None else max(max_time, current_time)
                        except ValueError:
                            pass
                        continue

                    code = ""
                    value = ""
                    first = line[0]
                    if first in "01xXzZ":
                        value = first
                        code = line[1:].strip()
                    elif first in "bBrR":
                        parts = line.split(maxsplit=1)
                        if len(parts) == 2:
                            value = parts[0][1:]
                            code = parts[1].strip()
                    if not code or code not in variables:
                        continue
                    changes[code] = changes.get(code, 0) + 1
                    if any(ch in value.lower() for ch in ("x", "z")):
                        xz_hits[code] = xz_hits.get(code, 0) + 1
        except OSError:
            return None

        if not variables:
            return None

        def unique_names(codes: list[str], limit: int = 5) -> list[str]:
            out: list[str] = []
            for code in codes:
                name = variables.get(code, {}).get("name", "")
                if name and name not in out:
                    out.append(name)
                if len(out) >= limit:
                    break
            return out

        changed_codes = [code for code in variables if changes.get(code, 0) > 1]
        clock_reset_codes = [
            code for code in changed_codes
            if re.search(r"\b(clk|clock|rst|reset)\b|clk|reset", variables[code]["name"], re.IGNORECASE)
        ]
        top_active_codes = sorted(
            [code for code in changed_codes if code not in clock_reset_codes],
            key=lambda c: changes.get(c, 0),
            reverse=True,
        )
        xz_codes = sorted(xz_hits, key=lambda c: xz_hits.get(c, 0), reverse=True)
        quiet_control_codes = [
            code for code, info in variables.items()
            if changes.get(code, 0) <= 1
            and re.search(r"valid|ready|done|state|irq|interrupt|ack|error|out", info["name"], re.IGNORECASE)
        ]

        observations: list[str] = []
        if max_time is not None:
            suffix = f" ({timescale} timescale)" if timescale else ""
            observations.append(f"Waveform activity reached simulation time {max_time}{suffix}.")
        if clock_reset_codes:
            observations.append("Clock/reset-like dumped signals toggled.")
        if xz_codes:
            observations.append(
                f"X/Z values appeared on {len(xz_codes)} design-like dumped signal(s); check reset/default assignments."
            )
        if quiet_control_codes:
            observations.append(
                f"{len(quiet_control_codes)} control/output-like dumped signal(s) stayed quiet; check enable, state, or output driving logic."
            )
        if not observations:
            observations.append("Waveform dump was present but did not expose a clear safe activity clue.")

        return {
            "timescale": timescale,
            "time_end": max_time,
            "signal_count": len(variables),
            "changed_signal_count": len(changed_codes),
            "clock_or_reset_activity": bool(clock_reset_codes),
            "unknown_or_high_impedance_count": len(xz_codes),
            "signals_with_unknowns": unique_names(xz_codes, 5),
            "quiet_control_like_signals": unique_names(quiet_control_codes, 5),
            "top_active_signals": unique_names(top_active_codes, 5),
            "observations": observations[:4],
        }

    @classmethod
    def _collect_waveform_observations(cls, private_root: Optional[Path]) -> dict:
        """Return compact waveform observations without paths, raw VCD, or harness data."""
        if private_root is None or not private_root.exists():
            return {"available": False, "observations": []}
        waveform_files: list[Path] = []
        for suffix in (".vcd", ".fst", ".ghw"):
            waveform_files.extend(private_root.rglob(f"*{suffix}"))
        if not waveform_files:
            return {"available": False, "observations": []}

        summaries: list[dict] = []
        skipped_large = 0
        for path in waveform_files[:MAX_WAVEFORM_FILES]:
            if path.suffix.lower() != ".vcd":
                continue
            summary = cls._summarize_vcd_file(path)
            if not summary:
                continue
            if summary.get("skipped_large"):
                skipped_large += 1
                continue
            summaries.append(summary)

        if not summaries:
            obs = ["Waveform artifact was produced, but no small parseable VCD summary was available."]
            if skipped_large:
                obs.append("At least one VCD was too large for runtime feedback and kept private for post hoc analysis.")
            return {
                "available": True,
                "files_seen": len(waveform_files),
                "files_analyzed": 0,
                "observations": obs[:2],
            }

        primary = summaries[0]
        return {
            "available": True,
            "files_seen": len(waveform_files),
            "files_analyzed": len(summaries),
            **primary,
        }

    @classmethod
    def _build_verify_feedback(
        cls,
        *,
        exit_code: int,
        stderr: str,
        service_results: list[dict],
        private_root: Optional[Path],
    ) -> dict:
        text = "\n".join(
            str(item.get("stderr", ""))
            for item in service_results
            if isinstance(item, dict)
        ) or stderr or ""
        passed = exit_code == 0
        tests_passed, tests_total = cls._parse_test_counts(text, passed)
        partial = 1.0 if passed else (tests_passed / tests_total if tests_total else 0.0)
        lower = text.lower()
        timeout = any(
            re.search(r"\b(timed out|timeout expired|deadline exceeded|exceeded .*timeout)\b", line.lower())
            for line in text.splitlines()
        )
        compile_bad = any(
            token in lower
            for token in (
                "syntax error",
                "elaboration",
                "compile error",
                "calledprocesserror",
                "returned non-zero exit status",
            )
        )
        sim_seen = any(token in lower for token in ("cocotb", "pytest", "test", "assert", "simulation"))
        if passed:
            failure_phase = "pass"
        elif compile_bad:
            failure_phase = "compile"
        elif timeout:
            failure_phase = "timeout"
        elif sim_seen:
            failure_phase = "functional_assertion"
        else:
            failure_phase = "verifier_failure"

        first_failure = ""
        for line in text.splitlines():
            low = line.lower()
            has_failure_detail = any(
                token in low for token in ("assert", "mismatch", "expected", "got")
            )
            if re.search(r"\btests\s*=\s*\d+\s+pass\s*=", low):
                continue
            if re.match(r"^[=\-_*\s]*(failures|errors|warnings|summary)?[=\-_*\s]*$", low):
                continue
            if "short test summary" in low or "test session starts" in low:
                continue
            if not has_failure_detail and re.search(r"\b\d+\s+passed\b|\b\d+\s+failed\b|\b\d+\s+errors?\b", low):
                continue
            if any(token in low for token in ("assert", "mismatch", "fail", "error", "expected", "got")):
                first_failure = cls._sanitize_verify_text(line, private_root=private_root)
                if first_failure:
                    break
        focus = {
            "pass": "The private verifier passed; keep changes minimal and stop.",
            "timeout": "Debug possible non-termination, clocks/resets, or combinational loops.",
            "compile": "Fix the first compile/elaboration issue before changing behavior.",
            "functional_assertion": "Debug the reported functional mismatch in visible RTL.",
            "verifier_failure": "Re-check edited RTL and visible task requirements; the verifier did not pass.",
        }.get(failure_phase, "Use the functional feedback to guide the next RTL edit.")

        return {
            "pass": passed,
            "partial_score": round(max(0.0, min(1.0, partial)), 4),
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "compile_ok": not compile_bad,
            "sim_ok": bool(passed or sim_seen),
            "timeout": timeout,
            "failure_phase": failure_phase,
            "failed_test_names": cls._failed_test_names(text),
            "first_failure": first_failure,
            "waveform_observations": cls._collect_waveform_observations(private_root),
            "suggested_next_focus": focus,
        }

    def _write_feedback_event(self, session: SessionState, event: dict) -> None:
        session.verifier_feedback_events.append(event)
        if not session.feedback_artifact_dir:
            return
        session.feedback_artifact_dir.mkdir(parents=True, exist_ok=True)
        event_path = session.feedback_artifact_dir / "verify_feedback_events.jsonl"
        with event_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    async def tool_verify_feedback(self, request: Request, body: VerifyFeedbackRequest) -> ToolResponse:
        session = self._get_session(request)
        reason = (body.reason or "").strip()

        def reject(code: str, message: str) -> ToolResponse:
            session.verifier_feedback_policy_violations += 1
            event = {
                "event": "verify_feedback_rejected",
                "code": code,
                "message": message,
                "reason": reason[:300],
                "call_count": session.verifier_feedback_calls,
                "write_count": session.write_count,
                "last_successful_compile_write_count": session.last_successful_compile_write_count,
                "timestamp": time.time(),
            }
            self._write_feedback_event(session, event)
            return ToolResponse(output=json.dumps({"error": code, "message": message}, ensure_ascii=False))

        if not self.config.runtime_verifier_feedback_enabled:
            return reject("verify_feedback_disabled", "verify_feedback is disabled for this rollout configuration.")
        max_calls = max(0, int(self.config.runtime_verifier_feedback_max_calls or 0))
        if session.verifier_feedback_calls >= max_calls:
            return reject("verify_feedback_budget_exhausted", f"verify_feedback call budget exhausted ({max_calls}).")
        if session.write_count <= 0:
            return reject("verify_feedback_requires_edit", "Call verify_feedback only after echo/edit changes visible code.")
        if session.last_successful_compile_write_count != session.write_count:
            return reject(
                "verify_feedback_requires_successful_iverilog",
                "Call verify_feedback only after a successful iverilog compile of the current edited code.",
            )
        if session.write_count_at_last_feedback == session.write_count:
            return reject(
                "verify_feedback_requires_new_edit",
                "Make a new code edit and successfully recompile before calling verify_feedback again.",
            )

        meta = CVDPAgenticHeavyVerifierMetadata.model_validate(session.verifier_metadata)
        scratch_root = _resolve_sandbox_root()
        private_root = Path(tempfile.mkdtemp(prefix=f"cvdp_verify_feedback_{meta.task_id}_", dir=str(scratch_root)))
        raw_log_path: Optional[Path] = None
        try:
            shutil.copytree(
                session.sandbox,
                private_root,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
            )
            async with self._semaphore:
                t0 = time.time()
                exit_code, stderr, service_results = await self._run_docker_harness(
                    sandbox=private_root,
                    harness_files=meta.harness_files,
                    task_id=meta.task_id,
                )
                execution_time = time.time() - t0

            session.verifier_feedback_calls += 1
            session.write_count_at_last_feedback = session.write_count
            if session.feedback_artifact_dir:
                session.feedback_artifact_dir.mkdir(parents=True, exist_ok=True)
                raw_log_path = session.feedback_artifact_dir / f"verify_feedback_call_{session.verifier_feedback_calls}.raw.log"
                raw_text = "\n".join(
                    f"[{item.get('service', 'service')} exit={item.get('exit_code')}]\n{item.get('stderr', '')}"
                    for item in service_results
                    if isinstance(item, dict)
                ) or stderr
                raw_log_path.write_text(raw_text, encoding="utf-8", errors="replace")

            feedback = self._build_verify_feedback(
                exit_code=exit_code,
                stderr=stderr,
                service_results=service_results,
                private_root=private_root,
            )
            event = {
                "event": "verify_feedback",
                "task_id": meta.task_id,
                "reason": reason[:300],
                "call_count": session.verifier_feedback_calls,
                "write_count": session.write_count,
                "sanitized_feedback": feedback,
                "raw_log_path": str(raw_log_path) if raw_log_path else None,
                "execution_time": execution_time,
                "timestamp": time.time(),
            }
            self._write_feedback_event(session, event)
            return ToolResponse(output=json.dumps({"verifier_feedback": feedback}, ensure_ascii=False))
        finally:
            shutil.rmtree(private_root, ignore_errors=True)

    # ------ Verification ------

    async def verify(self, request: Request, body: CVDPAgenticHeavyVerifyRequest) -> CVDPAgenticHeavyVerifyResponse:
        meta = CVDPAgenticHeavyVerifierMetadata.model_validate(body.verifier_metadata)
        category = meta.categories[0] if meta.categories else ""
        difficulty = meta.categories[1] if len(meta.categories) > 1 else ""

        session_id = request.session.get(SESSION_ID_KEY, "")
        session = self._sessions.get(session_id)
        sandbox = session.sandbox if session else None

        async with self._semaphore:
            t0 = time.time()
            exit_code, stderr, service_results = await self._run_docker_harness(
                sandbox=sandbox,
                harness_files=meta.harness_files,
                task_id=meta.task_id,
            )
            execution_time = time.time() - t0

        if session and session.verifier_feedback_events:
            self._write_feedback_event(
                session,
                {
                    "event": "final_verify",
                    "task_id": meta.task_id,
                    "final_pass": exit_code == 0,
                    "reward": 1.0 if exit_code == 0 else 0.0,
                    "verifier_feedback_calls": session.verifier_feedback_calls,
                    "verifier_feedback_policy_violations": session.verifier_feedback_policy_violations,
                    "timestamp": time.time(),
                },
            )

        # Clean up the session container after verification
        if session:
            await session.cleanup()
        self._sessions.pop(session_id, None)

        return CVDPAgenticHeavyVerifyResponse(
            **body.model_dump(),
            reward=1.0 if exit_code == 0 else 0.0,
            task_id=meta.task_id,
            category=category,
            difficulty=difficulty,
            docker_exit_code=exit_code,
            docker_stderr=stderr,
            docker_services=service_results,
            execution_time=execution_time,
        )

    async def _run_docker_harness(
        self,
        sandbox: Optional[Path],
        harness_files: Dict[str, Optional[str]],
        task_id: str,
    ) -> Tuple[int, str, List[Dict]]:
        """
        Write harness files to the sandbox and run docker compose for final grading.
        This uses docker compose (not docker exec) because the harness may define
        its own services, images, and entrypoints different from the tool container.
        """
        if sandbox is None:
            return 1, "No sandbox found for this session", []

        compose_content: Optional[str] = None
        for filepath, content in harness_files.items():
            if content is None:
                continue
            content = _apply_substitutions(content, self.config)
            if filepath.endswith("docker-compose.yml"):
                content = _filter_code_volumes(content)
                compose_content = content
            dest = sandbox / filepath
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")

        if compose_content is None:
            return 1, "No docker-compose.yml found in harness_files", []

        compose_data = yaml.safe_load(compose_content)
        services = list((compose_data.get("services") or {}).keys())

        service_results: List[Dict] = []
        for service in services:
            exit_code, output = await self._run_harness_service(str(sandbox), service, task_id)
            service_results.append({"service": service, "exit_code": exit_code, "stderr": output})

        final_exit_code = 0 if all(r["exit_code"] == 0 for r in service_results) else 1
        combined_stderr = "\n".join(f"[{r['service']}] {r['stderr']}" for r in service_results if r["stderr"])
        return final_exit_code, combined_stderr, service_results

    async def _run_harness_service(self, workdir: str, service: str, task_id: str) -> Tuple[int, str]:
        """Run a single docker compose service for final grading."""
        path = os.path.abspath(workdir)
        docker_file = os.path.join(path, "docker-compose.yml")
        project_name = _sanitize_docker_name(f"cvdp_ah_{task_id}_{int(time.time())}")

        uid = os.getuid()
        gid = os.getgid()

        cmd = [
            "docker", "compose", "-f", docker_file, "-p", project_name,
            "run", "--rm",
            "--user", f"{uid}:{gid}",
            "-e", "HOME=/code/rundir",
            "-w", "/code/rundir",
            "-v", f"{path}:/code",
            service,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=workdir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        exit_code = -1
        stdout_bytes = b""
        stderr_bytes = b""
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=self.config.docker_timeout,
            )
            exit_code = proc.returncode
        except asyncio.TimeoutError:
            proc.kill()
            stdout_bytes, stderr_bytes = await proc.communicate()
            exit_code = -1
            stderr_bytes = f"docker compose run timed out after {self.config.docker_timeout}s".encode()

        await self._cleanup_harness(docker_file, project_name, service)

        combined = (stderr_bytes + stdout_bytes).decode("utf-8", errors="replace")
        return exit_code, combined

    async def _cleanup_harness(self, docker_file: str, project_name: str, service: str) -> None:
        for cmd in [
            ["docker", "compose", "-f", docker_file, "-p", project_name, "kill", service],
            ["docker", "rmi", f"{project_name}-{service}"],
            ["docker", "network", "rm", f"{project_name}_default"],
        ]:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
                )
                await asyncio.wait_for(proc.wait(), timeout=30)
            except Exception:
                pass


if __name__ == "__main__":
    CVDPAgenticHeavyResourcesServer.run_webserver()
