"""Shared nested-context boundary and precise supplied-TB evidence parser."""
import re
from evaluation import command_state
CONTEXT_GUARD_CPP='''struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
'''

def mgen_score(event, log):
    status, reason = command_state(event, log, 'simulation')
    if status:
        return {'status': status, 'reason': reason, 'checks': None}
    clean = re.sub(r'\x1b\[[0-9;]*m', '', log)
    # Exact forms observed in supplied TBs; never accept a generic word Passed.
    successes = len(re.findall(r'\bTest\s*case Passed\b', clean, re.I))
    failures = len(re.findall(r'\bTest\s*case Failed\b', clean, re.I))
    failures += bool(re.search(r'\bTEST_FAIL\b|\bmismatch\b|\bFATAL\b|\bERROR:', clean, re.I))
    failures += any(int(value)>0 for pair in re.findall(r'\bMismatches:\s*(\d+)|\bFailed testcases:\s*(\d+)',clean,re.I) for value in pair if value)
    reports = re.findall(r'HARNESS_COUNTS checks=(\d+) failures=(\d+)', clean)
    if reports:
        checks, bad = map(int, reports[-1])
        if bad or failures:
            return {'status': 'fail', 'reason': 'explicit failed check overrides any success/count text', 'checks': checks}
        return {'status': 'pass' if checks > 0 else 'unknown', 'reason': 'completed supplied-TB count evidence', 'checks': checks}
    if failures:
        return {'status': 'fail', 'reason': 'explicit supplied-TB failed check', 'checks': successes + failures}
    return {'status': 'pass' if successes else 'unknown', 'reason': 'precise Test case/Testcase evidence' if successes else 'no recognized check evidence', 'checks': successes}
