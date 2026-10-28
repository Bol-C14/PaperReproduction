#!/usr/bin/env python3
"""Local-only dependency audit. Does not train, fetch, or run third-party code."""
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
report = {
    'python': platform.python_version(),
    'platform': platform.system() + ' ' + platform.release(),
    'executables': {x: shutil.which(x) for x in ['openroad', 'sta', 'yosys', 'nvidia-smi', 'pdftotext', 'git']},
    'modules': {x: importlib.util.find_spec(x) is not None for x in ['torch', 'transformers', 'numpy', 'matplotlib']},
    'experiments': {'candidate_trees': 0, 'sta_calls': 0, 'physical_evaluations': 0, 'sft_steps': 0, 'net_grpo_steps': 0, 'full_chip_feedback_steps': 0, 'external_model_api_calls': 0},
    'scope': 'Local readiness audit only; absence from PATH is not proof of absence elsewhere.',
}
report['git_version'] = subprocess.run(['git', '--version'], capture_output=True, text=True, check=True).stdout.strip()
path = root / 'metrics' / 'preflight.json'
path.write_text(json.dumps(report, indent=2) + '\n')
print(path.read_text(), end='')
