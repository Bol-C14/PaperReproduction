"""Run unchanged upstream evaluator; add subprocess logs without changing outcomes."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

output = Path(os.environ['P07_ORIGINAL_LOGDIR'])
real_run = subprocess.run
calls = []

def logged_run(*args, **kwargs):
    start = time.monotonic()
    i = len(calls)
    entry = {'command': str(args[0]), 'timeout_seconds': kwargs.get('timeout')}
    try:
        result = real_run(*args, **kwargs)
        entry['returncode'] = result.returncode
        (output / f'yosys_{i}.stdout.log').write_text(result.stdout or '')
        (output / f'yosys_{i}.stderr.log').write_text(result.stderr or '')
        return result
    except Exception as exc:
        entry['exception'] = type(exc).__name__
        raise
    finally:
        entry['wall_seconds'] = time.monotonic() - start
        calls.append(entry)
        (output / 'subprocess_calls.json').write_text(json.dumps(calls, indent=2))

subprocess.run = logged_run
sys.argv = ['/src/upstream/evaluation_script.py'] + sys.argv[1:]
runpy.run_path('/src/upstream/evaluation_script.py', run_name='__main__')
