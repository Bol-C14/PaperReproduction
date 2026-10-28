"""Independent restricted combinational evaluator; NOT the official evaluator."""
import csv
import json
import re
import resource
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = 'pcx_spc_grant_bufp1_pa_l'
OUTPUT = 'pcx_spc_grant_bufpdl_pa'

def assertion_block(rtl):
    marker = '// Assertion Start'
    if marker not in rtl or 'endmodule' not in rtl:
        return None
    return rtl[rtl.index(marker):rtl.rindex('endmodule')]

def normalize(line):
    return ''.join(line.split())

def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result

def evaluate(fixture, source):
    result = {'id': fixture['id'], 'text_match': None, 'cases_checked': 0}
    try:
        candidate = json.loads(fixture['response'], object_pairs_hook=unique_json_object)
    except (ValueError, TypeError):
        return result | {'status': 'INVALID_OUTPUT', 'reason': 'JSON parse failed'}
    if not isinstance(candidate, dict) or set(candidate) != {'CoT', 'buggy_code', 'correct_code'} or not all(isinstance(v, str) for v in candidate.values()):
        return result | {'status': 'INVALID_OUTPUT', 'reason': 'repair object schema mismatch'}
    line = candidate['correct_code']
    result['text_match'] = normalize(line) == normalize(source['fixed_line'])
    if '\n' in line or '\r' in line or not line.strip():
        return result | {'status': 'INVALID_OUTPUT', 'reason': 'replacement must be one nonempty line'}
    if candidate['buggy_code'] != source['buggy_line'] or fixture['rtl'].count(candidate['buggy_code']) != 1:
        return result | {'status': 'INVALID_OUTPUT', 'reason': 'buggy line not exact and unique'}
    if assertion_block(fixture['rtl']) != assertion_block(source['buggy_code']):
        return result | {'status': 'INVALID_CONTRACT', 'reason': 'assertion text changed or removed'}
    # No eval/exec, generated-code compilation, subprocess or network calls.
    assignment = re.fullmatch(r'\s*assign\s+' + OUTPUT + r'\s*=\s*(.*?)\s*;\s*', line)
    if not assignment:
        return result | {'status': 'UNKNOWN', 'reason': 'unsupported assignment grammar'}
    expression = re.sub(r'\s+', '', assignment.group(1))
    if expression == INPUT:
        operator, mask = 'xor', 0
    elif expression == '~' + INPUT:
        operator, mask = 'xor', 31
    else:
        xor = re.fullmatch(INPUT + r"\^5'b([01]{5})", expression)
        if not xor:
            return result | {'status': 'UNKNOWN', 'reason': 'unsupported expression; never credited'}
        operator, mask = 'xor', int(xor.group(1), 2)
    for value in range(32):
        if result['cases_checked'] >= fixture['case_budget']:
            return result | {'status': 'TIMEOUT', 'reason': 'port case budget exhausted; not an HDL solver timeout'}
        actual = (value ^ mask) & 31
        expected = (~value) & 31
        result['cases_checked'] += 1
        if actual != expected:
            return result | {'status': 'FAIL', 'reason': 'two-state functional counterexample', 'counterexample': {'input': value, 'actual': actual, 'expected': expected}}
    return result | {'status': 'PASS', 'reason': 'all 32 stable two-state input values satisfy inversion specification'}

def main():
    started = time.monotonic()
    source = json.loads((HERE / 'source_record.json').read_text())
    fixtures = json.loads((HERE / 'fixtures.json').read_text())
    if len(fixtures) > 10:
        raise ValueError('fixture cap exceeded')
    results = []
    for fixture in fixtures:
        try:
            result = evaluate(fixture, source)
        except Exception as exc:
            result = {'id': fixture['id'], 'status': 'ERROR', 'text_match': None, 'cases_checked': 0, 'reason': type(exc).__name__}
        result['expected_status'] = fixture['expected_status']
        result['expected_text_match'] = fixture['expected_text_match']
        result['expectations_met'] = result['status'] == fixture['expected_status'] and result['text_match'] == fixture['expected_text_match']
        results.append(result)
    summary = {'identity': 'independent restricted port; not official AssertSolver evaluation', 'fixtures': len(results), 'expectations_met': sum(r['expectations_met'] for r in results), 'statuses': dict(Counter(r['status'] for r in results)), 'text_matches': sum(r['text_match'] is True for r in results), 'functional_passes': sum(r['status'] == 'PASS' for r in results), 'wall_seconds': time.monotonic() - started, 'cpu_user_seconds': resource.getrusage(resource.RUSAGE_SELF).ru_utime, 'cpu_system_seconds': resource.getrusage(resource.RUSAGE_SELF).ru_stime, 'max_rss_KiB_linux': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, 'scope': 'one module; exhaustive 32-value stable two-state combinational behavior only'}
    (HERE / 'results.json').write_text(json.dumps({'summary': summary, 'results': results}, indent=2) + '\n')
    with (HERE / 'results.csv').open('w') as handle:
        writer = csv.writer(handle)
        writer.writerow(['fixture', 'text_match', 'status', 'cases_checked', 'expectations_met'])
        writer.writerows((r['id'], r['text_match'], r['status'], r['cases_checked'], r['expectations_met']) for r in results)
    print(json.dumps(summary, indent=2))
    for result in results:
        print(result['id'], 'text_match=' + str(result['text_match']), result['status'], 'expected=' + str(result['expectations_met']))
    return 0 if all(r['expectations_met'] for r in results) and not any(r['status'] == 'ERROR' for r in results) else 1

if __name__ == '__main__':
    sys.exit(main())
