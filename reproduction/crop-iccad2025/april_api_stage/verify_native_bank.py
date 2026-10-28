#!/usr/bin/env python3
"""Independent offline native-bank accounting and LUT/reference recheck; no tools/network."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys
import tempfile


def verify(root):
    src = Path(__file__).resolve().parents[1] / 'closed_loop'
    sys.path.insert(0, str(src))
    import study
    manifest = json.loads((src / 'manifest.json').read_text())
    bank = json.loads((root / 'bank.json').read_text())
    protocol = json.loads((root / 'protocol.json').read_text())
    rows = json.loads((root / 'results.json').read_text())
    designs = {d['id']: d for d in manifest['designs'] if d['role'] == 'prior'}
    expected = {(name, c['id']) for name in designs for c in manifest['configs']}
    assert len(rows) == len(expected) == 48
    assert {(r['design'], r['config']) for r in rows} == expected
    assert len({r['invocation'] for r in rows}) == 48
    assert protocol['real_api_calls'] == protocol['target_measurements'] == 0
    assert protocol['cpu_affinity'] == list(range(8, 16))
    assert bank['backend_relation'] == 'matched_native_archive'
    assert bank['tool_sha256'] == protocol['tool_sha256']
    assert bank['manifest_sha256'] == hashlib.sha256((src / 'manifest.json').read_bytes()).hexdigest()
    for name, design in designs.items():
        assert hashlib.sha256((root / design['rtl']).read_bytes()).hexdigest() == design['sha256']
        assert bank['history'][name] == sorted([r for r in rows if r['design'] == name],
                                              key=lambda r: (r['objective'], r['config']))
    counts = collections.Counter()
    for row in rows:
        folder = root / row['folder']
        assert folder.resolve().is_relative_to(root.resolve())
        assert row['status'] == 'ok' and row['synthesis_returncode'] == row['cec_returncode'] == 0
        assert 'Networks are equivalent' in (folder / 'cec.log').read_text()
        flow = (folder / 'flow.ys').read_text()
        mapping_abc = next(line.split()[2] for line in flow.splitlines() if line.startswith('abc -exe '))
        assert mapping_abc == row['commands'][1][0]
        check = study.verify_luts(folder / 'mapped.json', designs[row['design']])
        for key in ('lut_count', 'lut_depth', 'vectors_checked', 'vectors_sha256'):
            assert check[key] == row[key]
        assert row['objective'] == check['lut_count'] * check['lut_depth']
        counts['cec_positive_logs'] += 1
        counts['independent_vectors_rechecked'] += check['vectors_checked']
    example = next(r for r in rows if r['design'] == 'multiply')
    broken = json.loads((root / example['folder'] / 'mapped.json').read_text())
    broken['modules']['dut']['ports']['y']['bits'][0] = '1'
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'deliberately_invalid_output.json'
        path.write_text(json.dumps(broken))
        try:
            study.verify_luts(path, designs['multiply'])
        except ValueError:
            counts['corrupted_output_negative_control_rejected'] += 1
        else:
            raise AssertionError('Independent checker accepted a corrupted output')
    negative = json.loads((root / 'checks/negative_cec_result.json').read_text())
    log = (root / 'checks/negative_cec.log').read_text()
    assert negative['status'] == 'negative control rejected'
    assert negative['api_calls'] == negative['synthesis_calls'] == 0
    assert negative['cec_negative_calls'] == 1
    assert 'not equivalent' in log.lower() and 'Networks are equivalent' not in log
    counts['real_abc_negative_control_rejected'] = 1
    return dict(status='verified offline; no model or synthesis execution', measurement_rows=len(rows),
                source_commit=bank['source_commit'], **counts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parent / 'native_priors')
    args = parser.parse_args()
    print(json.dumps(verify(args.root), indent=2))
