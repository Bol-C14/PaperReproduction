"""Build only the ten fixtures reviewed in PROTOCOL.md; no code execution."""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent / 'P16-AssertSolver-source'
COMMIT = '96882fe018379d1974fd1e1b6c3b8f75e4de3d0e'
raw = subprocess.check_output(['git', '-C', str(REPO), 'show', f'{COMMIT}:testbench/SVA-Eval-Machine.json'])
record = next(r for r in json.loads(raw) if r['module_name'] == 'pcx_buf_pdl')
(HERE / 'source_record.json').write_text(json.dumps(record, indent=2) + '\n')
original = record['buggy_code']
assert original.count(record['buggy_line']) == 1
assert "1'b1 |-> pcx_spc_grant_bufpdl_pa == ~pcx_spc_grant_bufp1_pa_l" in original
output = 'pcx_spc_grant_bufpdl_pa'
input_ = 'pcx_spc_grant_bufp1_pa_l'

def response(line):
    return json.dumps({'CoT': 'Reviewed static fixture; no model inference.', 'buggy_code': record['buggy_line'], 'correct_code': line})

def fixture(id_, line, status, text, reason, rtl=None, budget=32):
    return {'id': id_, 'response': response(line), 'rtl': original if rtl is None else rtl, 'case_budget': budget, 'expected_status': status, 'expected_text_match': text, 'review_reason': reason}

correct = record['fixed_line']
fixtures = [
    fixture('01_released_fix', correct, 'PASS', True, 'Released replacement inverts all five bits.'),
    fixture('02_equivalent_xor', f"assign {output} = {input_} ^ 5'b11111;", 'PASS', False, 'Five-bit XOR with all ones is bitwise complement.'),
    fixture('03_unchanged_bug', record['buggy_line'], 'FAIL', False, 'Identity output differs from inversion for every two-state input.'),
    fixture('04_wrong_mask', f"assign {output} = {input_} ^ 5'b11110;", 'FAIL', False, 'Low bit is not inverted.'),
    fixture('05_false_antecedent', correct, 'INVALID_CONTRACT', True, 'False antecedent could evade an implication-only check.', rtl=original.replace("1'b1 |->", "1'b0 |->")),
    fixture('06_weakened_consequent', correct, 'INVALID_CONTRACT', True, 'Constant true replaces the output requirement.', rtl=original.replace(f'{output} == ~{input_}', "1'b1")),
    fixture('07_removed_assertion', correct, 'INVALID_CONTRACT', True, 'Removing the assertion skips its check.', rtl=original[:original.index('// Assertion Start')] + 'endmodule'),
    {'id': '08_malformed_json', 'response': '{not json', 'rtl': original, 'case_budget': 32, 'expected_status': 'INVALID_OUTPUT', 'expected_text_match': None, 'review_reason': 'Cannot parse candidate repair.'},
    fixture('09_unsupported_equivalent', f"assign {output} = 5'b11111 - {input_};", 'UNKNOWN', False, '31 minus a five-bit unsigned value equals its complement; subtraction is deliberately unsupported.'),
    fixture('10_budget_timeout', correct, 'TIMEOUT', True, 'Zero-case budget cannot establish exhaustive success.', budget=0),
]
assert len(fixtures) == 10
(HERE / 'fixtures.json').write_text(json.dumps(fixtures, indent=2) + '\n')
print('Built 10 pre-reviewed fixtures from one public record; no model or HDL execution.')
