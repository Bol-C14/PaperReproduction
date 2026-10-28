"""Abstract simulator base class and shared command execution helpers.

Timeouts, command failures, and missing tools are reported as error states
without interrupting the main evaluation flow.
"""
import subprocess
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)


class SimulatorBase(ABC):
    """Base class for simulator integrations such as Verilator or Xcelium."""

    def __init__(self, sim_config: Dict):
        self.config = sim_config
        self.tool = sim_config.get("tool", "vcs")
        self.compile_options = sim_config.get("compile_options", "")
        self.sim_options = sim_config.get("sim_options", "")
        self.timeout = sim_config.get("case_timeout", 300)
        self.coverage_cfg = sim_config.get("coverage", {})

    def _run_command(
        self,
        cmd: str,
        work_dir: Path,
        timeout: int = None,
        log_file: Path = None
    ) -> Tuple[int, str, str]:
        """Run a shell command with timeout control and optional log output.

        Returns ``(return_code, stdout, stderr)``. Return codes are 0 for
        success, -1 for timeout, -2 for execution failure, and positive values
        for errors reported by the command itself.
        """
        timeout = timeout or self.timeout
        try:
            result = subprocess.run(
                ["bash", "-c", cmd],
                cwd=str(work_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout
            )
            stdout = result.stdout
            stderr = result.stderr or ""
            ret_code = result.returncode

            # Save the log to a file.
            if log_file:
                try:
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    log_file.write_text(stdout + stderr, encoding="utf-8")
                except Exception as e:
                    logger.warning(f"Failed to save simulation log: {str(e)}")

            return ret_code, stdout, stderr

        except subprocess.TimeoutExpired:
            err_msg = f"Command timed out (>{timeout}s): {cmd[:80]}..."
            logger.warning(err_msg)
            return -1, "", err_msg
        except FileNotFoundError:
            err_msg = f"Command not found; the simulator may not be installed or on PATH: {cmd.split()[0]}"
            logger.warning(err_msg)
            return -2, "", err_msg
        except Exception as e:
            err_msg = f"Command execution failed: {str(e)}"
            logger.error(err_msg)
            return -2, "", err_msg

    @abstractmethod
    def compile(
        self,
        file_list: List[Path],
        work_dir: Path,
        top_module: str = "dut_tb",
        enable_coverage: bool = False
    ) -> Tuple[bool, str]:
        """Compile a design and return ``(success, compile_log)``."""
        pass

    @abstractmethod
    def run_simulation(
        self,
        work_dir: Path,
        simv_name: str = "simv"
    ) -> Tuple[bool, str, Dict]:
        """Run a simulation and return ``(success, log, result)``."""
        pass

    @abstractmethod
    def get_coverage(self, work_dir: Path) -> Dict:
        """Parse line, toggle, and functional coverage results."""
        pass
