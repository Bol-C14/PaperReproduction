"""Real simulator adapter with a global write-before-launch attempt ledger."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import math
import re
import resource
import subprocess
import time
import yaml

EXP = Path(__file__).resolve().parents[1]
PROJECT = EXP.parents[1]
CONFIG = json.loads((EXP/'configs/protocol.json').read_text())
SIM = PROJECT/'tools/ngspice/usr/bin/ngspice'
ENV = {'PATH':'/usr/bin:/bin','LC_ALL':'C','OMP_NUM_THREADS':'1',
       'OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False))

def load_task(circuit):
    if circuit not in CONFIG['circuits']:
        raise ValueError('Circuit outside frozen protocol')
    path = PROJECT/'upstream'/f'{circuit}.yaml'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == CONFIG['source_hashes'][path.name]
    cfg = yaml.safe_load(path.read_text())
    assert len(cfg['W_values']) == 9
    return cfg

def parse_specs(cfg):
    specs = []
    for clause in cfg['user_specs_metric'].split(' AND '):
        match = re.fullmatch(r'(\w+)\s*([<>])\s*([\d.eE+-]+)', clause)
        if not match:
            raise ValueError(f'Unsupported constraint {clause}')
        name, op, target = match.groups()
        specs.append((name, op, float(target)))
    return specs

def score(cfg, metrics):
    """No imputation: incomplete measurements receive null objective/violation."""
    valid = all(value is not None and math.isfinite(value) for value in metrics.values())
    positive = ['average_delay','dynamic_power'] if 'average_delay' in metrics else ['ugbw','power_dc']
    valid = valid and all(metrics.get(name) is not None and metrics[name] > 0 for name in positive)
    if not valid:
        return {'measurement_valid':False,'normalized_fom':None,'yaml_fom':None,
                'constraints':{name:None for name,_,_ in parse_specs(cfg)},
                'feasible':False,'constraint_violation':None}
    numerator, denominator = 1., 1.
    for name, op, target in parse_specs(cfg):
        if name == 'fom':
            continue
        assert target > 0
        if op == '>': numerator *= metrics[name]/target
        else: denominator *= metrics[name]/target
    fom = numerator/denominator
    checks, violation = {}, 0.
    for name, op, target in parse_specs(cfg):
        value = fom if name == 'fom' else metrics[name]
        checks[name] = bool(value > target if op == '>' else value < target)
        violation += max(0., (target-value)/target if op == '>' else (value-target)/target)
    if 'average_delay' in metrics:
        fallback = metrics['dc_gain_db']/(metrics['average_delay']*metrics['dynamic_power'])
    else:
        fallback = metrics['dc_gain_db']*metrics['ugbw']/metrics['power_dc']
    return {'measurement_valid':True,'normalized_fom':fom,'yaml_fom':fallback,
            'constraints':checks,'feasible':all(checks.values()),'constraint_violation':violation}

def incumbent(rows):
    valid = [r for r in rows if r['measurement_valid'] and r['status'].startswith('valid_')]
    if not valid:
        return None
    return max(valid, key=lambda r: (r['feasible'],
               r['normalized_fom'] if r['feasible'] else -r['constraint_violation'],
               r['normalized_fom']))

def render(circuit, indices, mode='corrected', export=False, refined=False):
    cfg = load_task(circuit)
    assert len(indices) == len(cfg['variable']) and all(type(i) is int and 0 <= i <= 8 for i in indices)
    variables = {name:cfg['W_values'][i] for name,i in zip(cfg['variable'], indices)}
    fmt = dict(cfg['params']) | variables
    for name,(base,mult) in cfg['width_scales'].items(): fmt[name] = variables[base]*mult
    fmt.update(pdk_lib_path=str(PROJECT/'tools/sky130_subset.lib.spice'),
               subckt_name=cfg['subckt_name'],
               inst_pins=' '.join(str(cfg['testbench_signals'][p]) for p in cfg['subckt_pins']))
    fmt['ota_subckt'] = cfg['ota_subckt_template'].format(**fmt)
    deck = cfg['testbench_template'].format(**fmt)
    deck = deck.replace('\n','\n.temp 27\n',1)
    if circuit == 'inverter' and mode == 'corrected':
        start,end = deck.index('* Measure propagation delays'),deck.index('print dynamic_power')
        deck = deck[:start]+'''* Measurement port: explicit opposite response edges, same thresholds
    meas tran tphl TRIG v(IN) VAL=0.9 RISE=1 TARG v(OUT) VAL=0.9 FALL=1
    meas tran tplh TRIG v(IN) VAL=0.9 FALL=1 TARG v(OUT) VAL=0.9 RISE=1
    let average_delay = (tplh + tphl)/2
    meas tran time_mean_power AVG power from=0 to=4n
    let dynamic_power_timeweighted = abs(time_mean_power - static_power_abs)
    print dynamic_power_timeweighted tphl tplh static_power_abs
    '''+deck[end:]
    if export:
        if circuit == 'inverter':
            deck = deck.replace('print dc_gain_db','''set wr_singlescale
    set wr_vecnames
    wrdata dc.tsv v(IN) v(OUT)
    print dc_gain_db''')
            deck = deck.replace('quit','''set wr_singlescale
    set wr_vecnames
    wrdata tran.tsv v(IN) v(OUT) power
    quit''')
        else:
            deck = deck.replace('print power_dc','print power_dc i(VDD) v(VOUT)')
            deck = deck.replace('quit','''let gain_mag = mag(vout_ac)
    set wr_singlescale
    set wr_vecnames
    wrdata ac.tsv gain_mag
    quit''')
    if refined:
        deck = deck.replace('tran 1p 4n','tran 0.5p 4n 0 0.5p')
        deck = deck.replace('ac dec 100 1 10g','ac dec 200 1 10g')
    return cfg, variables, deck

def child_limits():
    resource.setrlimit(resource.RLIMIT_AS,(CONFIG['process_memory_limit_bytes'],)*2)
    resource.setrlimit(resource.RLIMIT_CPU,(CONFIG['process_cpu_limit_seconds'],)*2)

def evaluate(circuit, indices, context, mode='corrected', export=False, refined=False):
    if (EXP/'results/PHASE_CLOSED.json').exists():
        raise RuntimeError('Optimization tranche is closed')
    now = dt.datetime.now(dt.timezone.utc)
    if now >= dt.datetime.fromisoformat(CONFIG['deadline_utc']):
        raise RuntimeError('Whole-phase deadline reached')
    assert hashlib.sha256((PROJECT/'tools/sky130_subset.lib.spice').read_bytes()).hexdigest() == CONFIG['selector_sha256']
    root = EXP/'logs/attempts'
    root.mkdir(exist_ok=True)
    number = len(list(root.glob('[0-9]*')))+1
    if number > CONFIG['max_simulator_attempts']:
        raise RuntimeError('Global attempted-process budget reached')
    cfg, variables, deck = render(circuit, list(indices), mode, export, refined)
    folder = root/f'{number:04d}'
    folder.mkdir()
    (folder/'circuit.spice').write_text(deck)
    command = [str(SIM),'-n','-b','circuit.spice']
    row = {'global_attempt':number,'utc':now.isoformat(),'circuit':circuit,'indices':list(indices),
           'variables':variables,'mode':mode,'export':export,'refined':refined,'context':context,
           'cwd':str(folder),'command':command,'timeout_seconds':CONFIG['process_timeout_seconds'],
           'deck_sha256':hashlib.sha256(deck.encode()).hexdigest(),
           'engine_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'status':'launch_pending'}
    save(folder/'attempt.json',row)
    start = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        proc = subprocess.run(command,cwd=folder,env=ENV,capture_output=True,text=True,
                              timeout=CONFIG['process_timeout_seconds'],preexec_fn=child_limits)
        stdout,stderr,code = proc.stdout,proc.stderr,proc.returncode
    except subprocess.TimeoutExpired as err:
        stdout = (err.stdout or b'').decode() if isinstance(err.stdout,bytes) else (err.stdout or '')
        stderr,code = str(err),None
    except OSError as err:
        stdout,stderr,code = '',str(err),None
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    (folder/'stdout.log').write_text(stdout)
    (folder/'stderr.log').write_text(stderr)
    def raw(name):
        matches = re.findall(rf'\b{re.escape(name)}\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)',stdout)
        value = float(matches[-1]) if matches else None
        return value if value is not None and math.isfinite(value) else None
    metrics = {}
    for name in cfg['metrics']:
        if name == 'fom': continue
        source = 'dynamic_power_timeweighted' if name == 'dynamic_power' and mode == 'corrected' else name
        value = raw(source)
        metrics[name] = None if value is None else value*float(cfg['metric_post'][name].get('scale',1))
    row.update(score(cfg,metrics))
    message = stdout+'\n'+stderr
    if code is None: status = 'tool_or_timeout_error'
    elif re.search(r'could not find|can.t open|undefined parameter|cannot find|no such.*model',message,re.I): status = 'pdk_or_model_error'
    elif code != 0 or re.search(r'timestep too small|singular matrix|doanalyses.*failed',message,re.I): status = 'solver_or_deck_error'
    elif not row['measurement_valid'] or re.search(r'\berror\b|\bfatal\b|no such vector',message,re.I): status = 'measurement_invalid'
    else: status = 'valid_feasible' if row['feasible'] else 'valid_infeasible'
    if not status.startswith('valid_'):
        # Parsed partial numbers are evidence only, never GP training labels.
        row.update(measurement_valid=False,feasible=False,normalized_fom=None,yaml_fom=None,constraint_violation=None)
    row.update(status=status,returncode=code,metrics=metrics,
               raw_metrics={name:raw(name) for name in cfg['metrics'] if name!='fom'},
               extra_raw_metrics={n:raw(n) for n in ['tphl','tplh','static_power_abs','time_mean_power','dynamic_power_timeweighted']},
               wall_seconds=time.monotonic()-start,
               child_cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
               child_peak_rss_kib_upper_bound=after.ru_maxrss,
               diagnostics=[s for s in message.splitlines() if re.search(r'warning|error|failed|fatal',s,re.I)])
    save(folder/'attempt.json',row)
    return row
