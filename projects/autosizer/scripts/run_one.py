"""One frozen reference-point simulator attempt. No upstream executable imports."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import resource
import subprocess
import time
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_COMMIT = 'beffdd177abc73392ba9bd6f51162ccf28fe7075'
parser = argparse.ArgumentParser()
parser.add_argument('circuit', choices=['inverter', 'five_trans_ota'])
parser.add_argument('variant', choices=['original', 'repaired_export'])
parser.add_argument('--diagnostic-refinement', action='store_true')
args = parser.parse_args()
budget = json.loads((ROOT / 'configs/budget.json').read_text())
now = dt.datetime.now(dt.timezone.utc)
if now >= dt.datetime.fromisoformat(budget['deadline_utc']):
    raise SystemExit('Setup/diagnosis time budget exhausted')
downloads = json.loads((ROOT / 'provenance/downloads.json').read_text())
if sum(x.get('bytes', 0) for x in downloads) > budget['max_download_bytes']:
    raise SystemExit('Download budget exhausted')
ledger_path = ROOT / 'logs/attempts.json'
ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
if len(ledger) >= budget['max_simulation_attempts']:
    raise SystemExit('Simulation-attempt budget exhausted')
cfg_path = ROOT / 'upstream' / (args.circuit + '.yaml')
cfg = yaml.safe_load(cfg_path.read_text())
values = {v: 1.68 for v in cfg['variable']}
fmt = dict(cfg['params'])
fmt.update(values)
for physical, (base, multiplier) in cfg['width_scales'].items():
    fmt[physical] = values[base] * multiplier
fmt.update(pdk_lib_path=str(ROOT / 'tools/sky130_subset.lib.spice'),
           subckt_name=cfg['subckt_name'],
           inst_pins=' '.join(str(cfg['testbench_signals'][pin]) for pin in cfg['subckt_pins']))
fmt['ota_subckt'] = cfg['ota_subckt_template'].format(**fmt)
deck = cfg['testbench_template'].format(**fmt)
deck = deck.replace('\n', '\n.temp 27\n', 1)
changes = ['PDK path/pin/parameter interpolation', 'explicit default temperature 27C']
if args.variant == 'repaired_export':
    if args.circuit == 'inverter':
        old = deck[deck.index('* Measure propagation delays'):deck.index('print dynamic_power')]
        new = '''    * Narrow repair: physically paired inverter response edges
    meas tran tphl TRIG v(IN) VAL=0.9 RISE=1 TARG v(OUT) VAL=0.9 FALL=1
    meas tran tplh TRIG v(IN) VAL=0.9 FALL=1 TARG v(OUT) VAL=0.9 RISE=1
    let average_delay = (tplh + tphl)/2
    meas tran time_mean_power AVG power from=0 to=4n
    let dynamic_power_timeweighted = abs(time_mean_power - static_power_abs)
    print dynamic_power_timeweighted avg_power_calc static_power_abs tphl tplh
    set wr_singlescale
    set wr_vecnames
    wrdata tran.tsv v(IN) v(OUT) power
'''
        deck = deck.replace(old, new)
        deck = deck.replace('print dc_gain_db', '''    set wr_singlescale
    set wr_vecnames
    wrdata dc.tsv v(IN) v(OUT)
    print dc_gain_db''')
        changes += ['pair opposite-direction propagation edges',
                    'report integral mean power alongside original sample mean', 'export DC/transient vectors']
    else:
        deck = deck.replace('print power_dc', 'print power_dc v(VOUT) v(xota.source) v(xota.net8) i(VDD)')
        deck = deck.replace('quit', '''    let gain_mag = mag(vout_ac)
    set wr_singlescale
    set wr_vecnames
    wrdata ac.tsv gain_mag
    quit''')
        changes += ['export AC magnitude and operating-point voltages; measurements unchanged']
if args.diagnostic_refinement:
    if args.circuit == 'inverter':
        deck = deck.replace('tran 1p 4n', 'tran 0.5p 4n 0 0.5p')
    else:
        deck = deck.replace('ac dec 100 1 10g', 'ac dec 200 1 10g')
    changes += ['diagnostic grid refinement; not a new benchmark result']
attempt_id = len(ledger) + 1
label = f'{attempt_id:02d}_{args.circuit}_{args.variant}'
if args.diagnostic_refinement:
    label += '_refined'
out = ROOT / 'logs' / label
out.mkdir()
deck_path = out / 'circuit.spice'
deck_path.write_text(deck)
command = [str(ROOT / 'tools/ngspice/usr/bin/ngspice'), '-n', '-b', 'circuit.spice']
row = {'attempt': attempt_id, 'utc': now.isoformat(), 'protocol_commit': PROTOCOL_COMMIT,
       'circuit': args.circuit, 'variant': args.variant,
       'diagnostic_refinement': args.diagnostic_refinement, 'status': 'launch_pending',
       'cwd': str(out), 'command': command, 'timeout_seconds': 90,
       'deck_sha256': hashlib.sha256(deck_path.read_bytes()).hexdigest(),
       'upstream_yaml_sha256': hashlib.sha256(cfg_path.read_bytes()).hexdigest(),
       'reference_base_widths': values, 'physical_parameters': fmt | {'ota_subckt': '[see deck]'},
       'changes': changes}
ledger.append(row)
ledger_path.write_text(json.dumps(ledger, indent=2))
start = time.monotonic()
env = {'PATH': '/usr/bin:/bin', 'OMP_NUM_THREADS': '1',
       'OPENBLAS_NUM_THREADS': '1', 'LC_ALL': 'C'}
try:
    proc = subprocess.run(command, cwd=out, env=env, capture_output=True, text=True, timeout=90)
    stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
except subprocess.TimeoutExpired as e:
    stdout = (e.stdout or b'').decode() if isinstance(e.stdout, bytes) else (e.stdout or '')
    stderr, code = str(e), None
except OSError as e:
    stdout, stderr, code = '', str(e), None
usage = resource.getrusage(resource.RUSAGE_CHILDREN)
(out / 'stdout.log').write_text(stdout)
(out / 'stderr.log').write_text(stderr)
row.update(wall_seconds=time.monotonic()-start, returncode=code,
           child_cpu_seconds=usage.ru_utime+usage.ru_stime,
           child_max_rss_kib=usage.ru_maxrss)
def metric(name):
    found = re.findall(rf'\b{re.escape(name)}\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)', stdout)
    value = float(found[-1]) if found else None
    return value if value is not None and math.isfinite(value) else None
names = cfg['metrics'][:-1]
metrics = {}
for name in names:
    raw = metric(name)
    metrics[name] = None if raw is None else raw * float(cfg['metric_post'][name].get('scale', 1))
extra = {name: metric(name) for name in ['tphl', 'tplh', 'dynamic_power_timeweighted',
                                      'avg_power_calc', 'static_power_abs', 'time_mean_power']}
diagnostics = [line for line in (stdout+'\n'+stderr).splitlines()
               if re.search(r'error|failed|fatal|no such|unknown|not found|no model|out of range', line, re.I)]
valid = all(value is not None for value in metrics.values())
if args.circuit == 'inverter':
    valid = valid and (metrics.get('average_delay') or -1) > 0 and (metrics.get('dynamic_power') or -1) > 0
    if valid:
        g,d,p = [metrics[n] for n in names]
        yaml_fom, normalized_fom = g/(d*p), (g/20)/((d/50)*(p/50))
else:
    valid = valid and (metrics.get('ugbw') or -1) > 0 and (metrics.get('power_dc') or -1) > 0
    if valid:
        g,f,p = [metrics[n] for n in names]
        yaml_fom, normalized_fom = g*f/p, ((g/15)*(f/10))/(p/65)
if not valid:
    yaml_fom, normalized_fom = None, None
checks = {}
for clause in cfg['user_specs_metric'].split(' AND '):
    m = re.fullmatch(r'(\w+)\s*([<>])\s*([\d.]+)', clause)
    name, op, target = m.groups()
    value = normalized_fom if name == 'fom' else metrics.get(name)
    checks[clause] = None if value is None else (value > float(target) if op == '>' else value < float(target))
if code is None:
    status = 'tool_or_timeout_error'
elif re.search(r'could not find|can.t open|undefined parameter|cannot find|no such.*model', stdout+stderr, re.I):
    status = 'pdk_or_model_error'
elif code != 0:
    status = 'solver_or_deck_error'
elif not valid or diagnostics:
    status = 'measurement_invalid'
else:
    status = 'valid_feasible' if all(checks.values()) else 'valid_infeasible'
row.update(status=status, raw_metrics={name: metric(name) for name in names},
           metrics=metrics, extra_raw_metrics=extra, yaml_fom=yaml_fom,
           controller_normalized_fom=normalized_fom, constraints_normalized=checks,
           yaml_fom_constraint_pass=None if yaml_fom is None else yaml_fom > (1 if args.circuit=='inverter' else 0.5),
           error_diagnostics=diagnostics)
ledger[-1] = row
ledger_path.write_text(json.dumps(ledger, indent=2))
(out / 'attempt.json').write_text(json.dumps(row, indent=2))
print(json.dumps({key: row[key] for key in ['attempt','circuit','variant','status','metrics',
                                        'yaml_fom','controller_normalized_fom','wall_seconds',
                                        'child_max_rss_kib','error_diagnostics']}, indent=2))
