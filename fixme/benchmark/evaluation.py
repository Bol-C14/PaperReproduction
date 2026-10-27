"""Content/tool-state based scoring shared by CLI and bounded regression checks."""
import json
import re
import signal


def command_state(event, log, phase):
    """Return an outcome only when the command did not complete its intended phase.

    Candidate syntax/type/link diagnostics are task failures. Missing dependencies,
    tool crashes and non-diagnostic nonzero exits are infrastructure errors.
    Time/resource exhaustion is unknown; it is never evidence of wrong function.
    """
    if event['status'] == 'timeout':
        return 'unknown', 'wall timeout'
    if event['status'] != 'completed' or event.get('returncode') is None:
        return 'error', 'execution or isolation setup failed'
    code = event['returncode']
    if code in [-signal.SIGXCPU, -signal.SIGKILL, -signal.SIGXFSZ]:
        return 'unknown', 'resource limit or external kill; no functional judgment'
    low = log.lower()
    # These must precede syntax diagnostics: missing headers/libs are infrastructure.
    if code in [126, 127] or re.search(r'command not found|cannot execute|error while loading shared libraries|cannot find -l|fatal error: .*no such file or directory', low):
        return 'error', 'tool or build dependency unavailable'
    if code < 0:
        return 'error', 'tool process terminated by signal'
    if code == 0:
        return None, ''
    if phase == 'compile' and re.search(r'syntax error|parse error|error:|%error|error\[', low):
        return 'fail', 'candidate compilation diagnostic'
    if phase == 'simulation' and re.search(r'test_fail|test case failed|some tests failed|fatal:', low):
        return 'fail', 'functional test failure reported'
    if phase == 'formal' and 'proof did fail' in low:
        return 'fail', 'formal counterexample reported'
    if phase == 'formal' and re.search(r'syntax error|parse error', low):
        return 'fail', 'candidate assertion syntax diagnostic'
    return 'error', 'nonzero tool exit without a recognized candidate diagnostic'


def simulation_score(event, log, marker, expected_checks=None):
    status, reason = command_state(event, log, 'simulation')
    if status:
        return dict(status=status, functional_pass=False if status == 'fail' else None,
                    reason=reason, official_status=status)
    official = event['returncode'] == 0 and (
        bool(re.search(r'TEST_PASS|test passed|PASS|All tests passed', log, re.I))
        or not bool(re.search(r'Error|FATAL|FAILED|assertion failed', log, re.I)))
    checks = len(re.findall('Test case Passed', log))
    bad = bool(re.search(r'TEST_FAIL|Test case Failed|SOME TESTS FAILED|ERROR:|FATAL', log, re.I))
    success = marker in log and not bad and (expected_checks is None or checks == expected_checks)
    return dict(status='pass' if success else 'fail', functional_pass=success,
                reason='explicit test evidence' if success else 'missing success/check evidence or observed mismatch',
                observed_checks=checks if expected_checks is not None else None,
                official_status='pass' if official else 'fail')


def clean_response(raw):
    # Extraction is intentionally deterministic; comments cannot claim supported syntax.
    from src.evaluators.eval_utils import extract_code_block
    code = extract_code_block(raw, 'verilog')
    return re.sub(r'/\*.*?\*/|//[^\n]*', '', code, flags=re.S).strip()


def unsupported_sva_reason(code):
    if re.search(r'\b(property|sequence|posedge|negedge|disable|throughout|within|until|s_eventually|assume|restrict|cover)\b|\|[-=]>|##|\$past|\$rose|\$fell|\$stable', code):
        return 'response uses temporal SVA or assumptions outside the immediate combinational adapter'
    # No semantic rewriting of unrecognized constructs; parser handles malformed syntax.
    return None


def property_counts(design_path):
    """Count actual lowered Yosys cells, not tokens in response or fixture labels."""
    design = json.loads(design_path.read_text())
    counts = {'assert': 0, 'assume': 0, 'cover': 0}
    for mod in design['modules'].values():
        for cell in mod.get('cells', {}).values():
            typ = cell['type']
            for key in counts:
                if typ == '$' + key:
                    counts[key] += 1
    return counts


def formal_score(event, log, counts, mutation_killed=None):
    status, reason = command_state(event, log, 'formal')
    if status:
        return dict(status=status, functional_pass=False if status == 'fail' else None, reason=reason)
    if counts is None:
        return dict(status='error', functional_pass=None, reason='missing/unreadable actual formal design')
    if counts['assume']:
        return dict(status='unsupported', functional_pass=None, reason='assumptions are outside unconstrained pilot proof')
    if counts['assert'] == 0:
        return dict(status='unknown', functional_pass=None, reason='vacuous: zero actual assertion properties')
    if 'SUCCESS!' not in log:
        return dict(status='unknown', functional_pass=None, reason='no recognized proof completion')
    if mutation_killed is not True:
        return dict(status='unknown', functional_pass=None, reason='vacuity/adequacy gate: selected CRC output mutant was not falsified')
    return dict(status='pass', functional_pass=True, reason='nonzero properties proven and selected output mutant falsified')
