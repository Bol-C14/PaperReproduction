#!/usr/bin/env python3
"""CPU-only native prior-bank preparation. No model imports or network calls.

Separate from the paused live entry point. Measures six public prior circuits,
eight configurations each, preserving CEC and independent reference checks.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time


def main():
    root = Path(os.environ['PAPER_REPRO_ROOT']).resolve()
    src = Path(__file__).resolve().parents[1] / 'closed_loop'
    sys.path.insert(0, str(src))
    import study
    out = root / 'results/crop/native-priors'
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((src / 'manifest.json').read_text())
    tools = {'yosys': root / 'tools/crop/yosys/yosys', 'abc': root / 'tools/abc-rl/abc/abc'}
    # Reuse the prepared native tools; do not install, rebuild or modify them.
    tool_sha256 = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in tools.items()}
    prior_designs = [d for d in manifest['designs'] if d['role'] == 'prior']
    source_commit = subprocess.check_output(['git', '-C', str(src), 'rev-parse', 'HEAD'], text=True).strip()
    study.dump(out / 'protocol.json', dict(source_commit=source_commit, kind='non-model native archive preparation',
        max_measurement_attempts=48, prior_circuits=6, configs_per_prior=8, target_measurements=0,
        real_api_calls=0, formal='ABC CEC required per measurement', independent_vectors_per_measurement=256,
        correctness_seed=manifest['correctness_seed'], tool_sha256=tool_sha256,
        cpu_affinity=sorted(os.sched_getaffinity(0)), python=platform.python_version(),
        thread_caps={k: os.environ.get(k) for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')},
        frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
    for design in prior_designs:
        if hashlib.sha256((src / design['rtl']).read_bytes()).hexdigest() != design['sha256']:
            raise SystemExit('Public prior source differs from manifest')
    for name in ('circuits', 'abc_scripts'):
        shutil.copytree(src / name, out / name)
    study.dump(out / 'manifest.json', dict(manifest, max_measurement_calls=48))
    study.ROOT, study.YOSYS, study.ABC = out, tools['yosys'], tools['abc']
    st = study.Study()
    for design in prior_designs:
        for config in manifest['configs']:
            row = st.measure(design, config, 'native_prior')
            if row['status'] != 'ok':
                raise SystemExit('Native prior measurement failed; stop and retain evidence')
    history = {d['id']: sorted([r for r in st.rows if r['design'] == d['id']],
                key=lambda r: (r['objective'], r['config'])) for d in prior_designs}
    historical = json.loads((src / 'history.json').read_text())
    comparisons = []
    for name, rows in history.items():
        old = {r['config']: r for r in historical[name]}
        fresh_c0 = next(r['objective'] for r in rows if r['config'] == 'c0')
        old_c0 = old['c0']['objective']
        for row in rows:
            previous = old[row['config']]
            comparisons.append(dict(design=name, config=row['config'],
                historical_luts=previous['lut_count'], historical_depth=previous['lut_depth'],
                native_luts=row['lut_count'], native_depth=row['lut_depth'],
                historical_ratio_to_c0=previous['objective']/old_c0,
                native_ratio_to_c0=row['objective']/fresh_c0,
                raw_metrics_equal=(row['lut_count'], row['lut_depth']) == (previous['lut_count'], previous['lut_depth'])))
    study.dump(out / 'bank.json', dict(source_commit=source_commit, backend_relation='matched_native_archive',
        manifest_sha256=hashlib.sha256((src/'manifest.json').read_bytes()).hexdigest(),
        tool_sha256=tool_sha256, history=history))
    study.dump(out / 'comparison.json', dict(measurements=48, target_measurements=0, real_api_calls=0,
        cec_passes=48, independent_vector_checks=48*256,
        identical_metric_pairs=sum(r['raw_metrics_equal'] for r in comparisons), total_pairs=48,
        comparisons=comparisons,
        conclusion='Use only the matched native bank for future model guidance. Historical rows remain untouched; no cross-backend pooling.'))
    print('NATIVE_BANK_COMPLETE', len(st.rows), flush=True)


if __name__ == '__main__':
    main()
