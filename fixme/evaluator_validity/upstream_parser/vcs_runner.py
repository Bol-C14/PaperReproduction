"""Synopsys VCS simulator wrapper."""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

from .simulation_base import SimulatorBase

logger = logging.getLogger(__name__)


class VCSRunner(SimulatorBase):
    """Wrap VCS compilation, simulation, and URG coverage parsing."""

    COVERAGE_KEY_ALIASES = {
        "line": "line",
        "ln": "line",
        "cond": "condition",
        "condition": "condition",
        "conditional": "condition",
        "fsm": "fsm",
        "state": "fsm",
        "state_machine": "fsm",
        "statemachine": "fsm",
        "toggle": "toggle",
        "tgl": "toggle",
        "tog": "toggle",
    }

    def __init__(self, sim_config: Dict):
        super().__init__(sim_config)
        self.vcs_path = sim_config.get("vcs_path", "")
        self.vcs_cmd = f"{self.vcs_path}vcs" if self.vcs_path else "vcs"
        self.urg_cmd = f"{self.vcs_path}urg" if self.vcs_path else "urg"

    @classmethod
    def _normalize_coverage_keys(cls, coverage: Dict[str, float]) -> Dict[str, float]:
        """Normalize URG metric aliases to report keys."""
        normalized = {}
        for key, value in coverage.items():
            canonical = cls.COVERAGE_KEY_ALIASES.get(str(key).strip().lower())
            if canonical:
                normalized[canonical] = value
        return normalized

    @staticmethod
    def _parse_coverage_report(report_text: str) -> Dict[str, float]:
        """Parse both labeled and tabular URG text summaries."""
        aliases = VCSRunner.COVERAGE_KEY_ALIASES

        lines = [line.strip() for line in report_text.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            headers = re.findall(r"[A-Za-z]+", line.upper())
            positions = {
                aliases[header.lower()]: next(
                    (pos for pos, item in enumerate(headers) if item == header),
                    None,
                )
                for header in headers
                if header.lower() in aliases
            }
            if not positions:
                continue

            for value_line in lines[index + 1:index + 5]:
                values = re.findall(r"(?:\d+(?:\.\d+)?|--|N/A)", value_line.upper())
                if len(values) < len(headers):
                    continue
                parsed = {}
                for metric, position in positions.items():
                    value = values[position]
                    if value not in {"--", "N/A"}:
                        parsed[metric] = float(value)
                if parsed:
                    return VCSRunner._normalize_coverage_keys(parsed)

        parsed = {}
        patterns = {
            "line": r"\bLine(?:\s+Coverage)?[^%\d]{0,40}(\d+\.?\d*)%",
            "condition": r"\b(?:Condition|Cond)(?:\s+Coverage)?[^%\d]{0,40}(\d+\.?\d*)%",
            "fsm": r"\bFSM(?:\s+Coverage)?[^%\d]{0,40}(\d+\.?\d*)%",
            "toggle": r"\b(?:Toggle|Tgl)(?:\s+Coverage)?[^%\d]{0,40}(\d+\.?\d*)%",
        }
        for metric, pattern in patterns.items():
            match = re.search(pattern, report_text, re.IGNORECASE)
            if match:
                parsed[metric] = float(match.group(1))
        return VCSRunner._normalize_coverage_keys(parsed)

    @staticmethod
    def _parse_coverage_xml(xml_text: str) -> Dict[str, float]:
        """Parse URG session.xml metric ratios into percentages."""
        metric_map = VCSRunner.COVERAGE_KEY_ALIASES
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return {}

        coverage = {}
        for metric in root.iter():
            if metric.tag.lower() != "metric":
                continue
            name = metric.attrib.get("name", "").strip().lower()
            key = metric_map.get(name)
            if not key:
                continue
            value = metric.attrib.get("value", "").strip()
            match = re.fullmatch(r"(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)", value)
            if not match:
                continue
            covered = float(match.group(1))
            total = float(match.group(2))
            if total > 0:
                coverage[key] = round(covered / total * 100, 2)
        return VCSRunner._normalize_coverage_keys(coverage)

    def compile(
        self,
        file_list: List[Path],
        work_dir: Path,
        top_module: str = "dut_tb",
        enable_coverage: bool = False,
    ) -> Tuple[bool, str]:
        """Compile Verilog/SystemVerilog files with VCS."""
        if not file_list:
            err_msg = "The compile file list is empty; compilation cannot run"
            logger.warning(err_msg)
            return False, err_msg

        if not work_dir.exists():
            try:
                work_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                err_msg = f"Failed to create the compile working directory: {str(e)}"
                logger.warning(err_msg)
                return False, err_msg

        valid_files = [
            path.resolve()
            for path in file_list
            if path.exists() and path.is_file()
        ]
        if len(valid_files) < len(file_list):
            missing = [path for path in file_list if not path.exists()]
            logger.warning(f"Some compile files do not exist and were filtered out: {missing}")
        if not valid_files:
            err_msg = "None of the compile files exist"
            logger.warning(err_msg)
            return False, err_msg

        filelist_path = work_dir / "dut.f"
        try:
            filelist_path.write_text(
                "\n".join(str(path) for path in valid_files) + "\n",
                encoding="utf-8",
            )
        except Exception as e:
            err_msg = f"Failed to write the VCS filelist: {str(e)}"
            logger.warning(err_msg)
            return False, err_msg

        compile_cmd = (
            f"{self.vcs_cmd} "
            f"{self.compile_options} "
            f"-f {filelist_path.name} "
            f"-top {top_module} "
            f"-o simv"
        )

        if enable_coverage and self.coverage_cfg.get("enable", False):
            cov_types = []
            if self.coverage_cfg.get("line"):
                cov_types.append("line")
            if self.coverage_cfg.get("condition"):
                cov_types.append("cond")
            if self.coverage_cfg.get("fsm"):
                cov_types.append("fsm")
            if self.coverage_cfg.get("toggle"):
                cov_types.append("tgl")
            if cov_types:
                compile_cmd += f" -cm {'+'.join(cov_types)} -cm_dir simv.vdb"

        log_file = work_dir / "compile.log"
        ret_code, stdout, stderr = self._run_command(
            compile_cmd,
            work_dir,
            log_file=log_file,
        )

        log_prefix = (
            f"Command: {compile_cmd}\n"
            f"Working directory: {work_dir.resolve()}\n"
            f"Filelist: {filelist_path.name}\n"
            f"{filelist_path.read_text(encoding='utf-8', errors='ignore')}\n"
        )
        log_content = log_prefix + stdout + stderr
        if log_file:
            try:
                log_file.write_text(log_content, encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to save the VCS compile log: {str(e)}")
        # VCS banner/license text contains ordinary "error" words; use return code
        # for compile status so successful compile/elab/link can proceed to sim.
        success = ret_code == 0

        if not success:
            logger.debug(f"VCS compilation failed with return code {ret_code}")
        return success, log_content

    def run_simulation(
        self,
        work_dir: Path,
        simv_name: str = "simv",
    ) -> Tuple[bool, str, Dict]:
        """Run the simv executable generated by VCS."""
        simv_path = work_dir / simv_name
        if not simv_path.exists():
            err_msg = "The simulation executable does not exist; compilation may have failed"
            logger.warning(err_msg)
            return False, err_msg, {"return_code": -1}

        sim_cmd = f"./{simv_name} {self.sim_options}"
        if self.coverage_cfg.get("enable", False):
            cov_types = []
            if self.coverage_cfg.get("line"):
                cov_types.append("line")
            if self.coverage_cfg.get("condition"):
                cov_types.append("cond")
            if self.coverage_cfg.get("fsm"):
                cov_types.append("fsm")
            if self.coverage_cfg.get("toggle"):
                cov_types.append("tgl")
            if cov_types:
                sim_cmd += f" -cm {'+'.join(cov_types)} -cm_dir simv.vdb"

        log_file = work_dir / "simulation.log"
        ret_code, stdout, stderr = self._run_command(
            sim_cmd,
            work_dir,
            log_file=log_file,
        )

        log_content = stdout + stderr
        sim_result = {"return_code": ret_code}

        # VCS reports a normal `$finish` as an "ERROR" block even when the
        # testbench has completed successfully. Exclude only that known block
        # before checking for actual simulator or test failures.
        error_log = re.sub(
            r"^\s*ERROR:\s*(?:[^\r\n]*\r?\n\s*)?\$finish called from file[^\r\n]*"
            r"(?:\r?\n\s*\$finish at simulation time[^\r\n]*)?",
            "",
            log_content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        has_error = bool(
            re.search(r"(Error|FATAL|FAILED|assertion failed)", error_log, re.IGNORECASE)
        )
        has_test_pass = bool(
            re.search(r"(TEST_PASS|test passed|PASS|All tests passed)", log_content, re.IGNORECASE)
        )

        success = (ret_code == 0) and (has_test_pass or not has_error)
        sim_result["has_test_pass"] = has_test_pass
        sim_result["has_error"] = has_error

        if not success:
            logger.debug(f"VCS simulation failed with return code {ret_code}")
        return success, log_content, sim_result

    def get_coverage(self, work_dir: Path) -> Dict:
        """Run URG and parse line, condition, FSM, and toggle coverage."""

        vdb_dir = work_dir / "simv.vdb"
        if not vdb_dir.exists():
            logger.warning("Coverage database not found; coverage is unavailable")
            return {}

        report_dir = work_dir / "coverage_report"
        report_file = work_dir / "coverage_report.txt"
        urg_cmd = (
            f"{self.urg_cmd} -line nocasedef -dir simv.vdb "
            f"-report {report_dir.name} -format both -show brief"
        )

        ret_code, _, _ = self._run_command(urg_cmd, work_dir)
        if ret_code != 0 or not report_dir.exists():
            logger.warning("Failed to generate the coverage report; coverage is unavailable")
            return {}

        try:
            if report_dir.is_file():
                report_text = report_dir.read_text(encoding="utf-8", errors="ignore")
            else:
                report_parts = sorted(report_dir.rglob("*.txt"))
                if not report_parts:
                    logger.warning("No text report found in the URG report directory; coverage is unavailable")
                    return {}
                report_text = "\n".join(
                    path.read_text(encoding="utf-8", errors="ignore")
                    for path in report_parts
                )
            report_file.write_text(report_text, encoding="utf-8")
            coverage = {}
            if report_dir.is_dir():
                for xml_path in sorted(report_dir.rglob("session.xml")):
                    coverage.update(
                        self._parse_coverage_xml(
                            xml_path.read_text(encoding="utf-8", errors="ignore")
                        )
                    )
                    if all(
                        key in coverage
                        for key in ("line", "condition", "toggle")
                    ):
                        break
            text_coverage = self._parse_coverage_report(report_text)
            for key, value in text_coverage.items():
                coverage.setdefault(key, value)
            coverage = self._normalize_coverage_keys(coverage)
            if "fsm" not in coverage:
                coverage["fsm"] = None
            missing = [
                key for key in ("line", "condition", "toggle")
                if key not in coverage
            ]
            if missing:
                logger.warning("URG coverage fields could not be parsed: %s", ", ".join(missing))
            return coverage

        except Exception as e:
            logger.warning(f"Failed to parse the coverage report: {str(e)}; coverage is unavailable")
            return {}
