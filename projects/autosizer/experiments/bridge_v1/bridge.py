"""Real ngspice bridge; the executable only permits a labeled test controller.
Reuses local frozen engine render/score and numerical GP-UCB, never its closed runner.
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import itertools
import json
import math
import os
import re
import resource
import subprocess
import sys
import time
import numpy as np
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT/'experiments/optimization_v1/scripts'))
from engine import render, score, load_task, incumbent
from search import propose_gp
sys.path.insert(0, str(PROJECT/'april_api_stage'))
from api_controller import validate, CU_FIELDS, OpenAICompatibleController

CFG = load_task('inverter')
VARIABLES = tuple(CFG['variable'])
VALUES = CFG['W_values']
ENV = {'PATH':'/usr/bin:/bin','LC_ALL':'C','OMP_NUM_THREADS':'1',
       'OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def public_row(row):
    keys = ('attempt','indices','variables','status','metrics','normalized_fom',
            'constraints','feasible','constraint_violation','measurement_valid')
    return {k:row[k] for k in keys}

def domain_points(value, seen=(), required=12):
    validate('initial_search_space', value)
    cfg = value['optimization_configuration']
    active, fixed = cfg['variables_to_optimize'], cfg['variables_fixed']
    choices = []
    for name in VARIABLES:
        if name in active:
            choices.append([VALUES.index(v) for v in active[name]['search_space']])
        else:
            info = fixed[name]
            choices.append([VALUES.index(info['fixed_value'] if isinstance(info,dict) else info)])
    points = sorted(itertools.product(*choices))
    unseen = [p for p in points if p not in set(map(tuple,seen))]
    if len(unseen) < required:
        raise ValueError(f'Domain has {len(unseen)} unseen points; {required} required')
    return points

def feedback(history, domain):
    valid = [r for r in history if r['measurement_valid']]
    best = incumbent(history)
    axes = [sorted({p[j] for p in domain}) for j in range(2)]
    top = sorted(valid,key=lambda r:(r['feasible'],r['normalized_fom'] if r['feasible'] else -r['constraint_violation']),reverse=True)[:5]
    return {'attempts':len(history),'valid':len(valid),'invalid':len(history)-len(valid),
            'feasible':sum(r['feasible'] for r in history),
            'incumbent':None if best is None else public_row(best),
            'boundary':[{'variable':name,'indices':axis,'top_indices':[r['indices'][j] for r in top],
                         'lower_count':sum(r['indices'][j]==axis[0] for r in top),
                         'upper_count':sum(r['indices'][j]==axis[-1] for r in top)}
                        for j,(name,axis) in enumerate(zip(VARIABLES,axes))]}

def request(stage, history, understanding=None, domain=None):
    # Allowlist public source fields; never serialize runtime configuration or arbitrary rows.
    context = {k:CFG[k] for k in ('ota_subckt_template','params','width_scales','W_values','user_specs_metric','metric_post')}
    context['testbench_template'] = CFG['testbench_template'].replace('{pdk_lib_path}','PUBLIC_SKY130_TT_SELECTOR')
    context.update(measurement_port='opposite-direction paired response edges; integral mean supply power minus static estimate; 27 C',
                   normalization='(dc_gain_db/20)/((average_delay_ps/50)*(dynamic_power_uW/50))',
                   understanding=understanding, history=[public_row(r) for r in history],
                   domain=domain,feedback=None if domain is None else feedback(history,domain),
                   batch_attempts=12,remaining_attempts=24-len(history),
                   gp_port='10 random initialization points; then fixed Constant(1)*Matern(nu=2.5,length_scale=.35)+WhiteKernel(1e-6), UCB mean+2sd; indices/8; normalize_y; no hyperparameter fitting; invalid excluded')
    instruction = {'circuit_understanding':'Return nonempty fields: '+', '.join(CU_FIELDS),
        'initial_search_space':'Return optimization_configuration: variables_to_optimize {name:{search_space:[released values]}}, variables_fixed {name:{fixed_value:released value}}, reasoning and search_space_summary. Cover each variable once. At least 12 unseen combinations.',
        'outer_regeneration':'Reflect on actual measured history and boundary feedback. Return same domain schema as initial_search_space, covering both variables exactly once with >=12 unseen combinations; explain change or honest no-change.',
        'inner_iteration':'Return {action:search|stop,method:random|bayesian,n_samples:12,parameters:{},reasoning:nonempty string}. No parameter overrides. Stop is honored. Bayesian is the disclosed numerical port.'}[stage]
    return [{'role':'system','content':'AutoSizer integration pilot. Return exactly one JSON object. Use supplied public circuit and new measured feedback only. Never invent simulations.'},
            {'role':'user','content':json.dumps({'stage':stage,'instruction':instruction,'context':context},separators=(',',':'))}]

class TestController:
    """Deterministic software fixture, not a model and not paper evidence."""
    label = 'TEST_CONTROLLER_NOT_LLM'
    def call(self, *, stage, messages, **unused):
        context = json.loads(messages[-1]['content'])['context']
        if stage == 'circuit_understanding':
            return {k:'TEST FIXTURE ONLY: two-device inverter with coupled p/n widths; no model analysis.' for k in CU_FIELDS}
        if stage == 'inner_iteration':
            return {'action':'search','method':'random' if not context['history'] else 'bayesian',
                    'n_samples':12,'parameters':{},'reasoning':'TEST FIXTURE ONLY: exercise random then GP dispatch.'}
        indices = list(range(1,8)) if stage=='initial_search_space' else list(range(9))
        if stage=='outer_regeneration' and len(context['history'])!=12:
            raise ValueError('Fixture requires twelve real new measurements before reflection')
        return {'optimization_configuration':{'variables_to_optimize':{name:{'search_space':[VALUES[i] for i in indices]} for name in VARIABLES},'variables_fixed':{}},
                'search_space_summary':{'test_fixture':True},
                'reasoning':'TEST FIXTURE ONLY: central domain initially; expand after actual twelve-row feedback.'}

class APIBridgeController:
    """Deferred integration only. No CLI enables this backend.

    Parent authorization, designated runtime values and a model-specific local token
    counter are mandatory. The counter must include chat framing, not just content.
    """
    label = 'API_CONTROLLER_BACKEND_SUBSTITUTION'
    caps = {'circuit_understanding':1536,'initial_search_space':768,
            'inner_iteration':256,'outer_regeneration':768}
    def __init__(self, *, adapter=None, authorized=False, token_counter=None, evidence_dir=None):
        if not authorized:raise RuntimeError('Endpoint/model/credential/public-payload authorization pending')
        if token_counter is None or evidence_dir is None:
            raise ValueError('Model-specific chat token counter and evidence directory required')
        self.adapter = adapter or OpenAICompatibleController(authorized=True,max_calls=10)
        self.token_counter, self.evidence_dir = token_counter,Path(evidence_dir)
    def call(self, *, stage,messages):
        context = json.loads(messages[-1]['content'])['context']
        for attempt in range(2):
            if self.adapter.calls>=10:raise RuntimeError('Ten attempted-request cap reached')
            count = self.token_counter(messages)
            if type(count) is not int or not 0<count<=8192:
                raise ValueError('Input chat-token cap exceeded or counter invalid')
            value = None
            try:
                value = self.adapter.call(stage=stage,messages=messages,max_tokens=self.caps[stage],
                                          remaining=context['remaining_attempts'],evidence_dir=self.evidence_dir)
                if stage in ('initial_search_space','outer_regeneration'):
                    domain_points(value,[r['indices'] for r in context['history']])
                if stage=='inner_iteration' and value['action']=='search' and value['n_samples']!=12:
                    raise ValueError('Fixed pilot requires twelve attempts')
                return value
            except ValueError as error:
                # Only local JSON/schema/domain errors are eligible; no transport retries.
                folder = self.evidence_dir/f'call_{self.adapter.calls:02d}'
                save(folder/'bridge_validation_error.json',{'type':'ValueError','message':str(error)})
                if attempt:raise
                response = folder/'response.txt'
                raw = response.read_text() if response.exists() else json.dumps(value)
                messages = messages+[{'role':'assistant','content':raw},
                                     {'role':'user','content':'Correct JSON/schema/domain error: '+str(error)}]

class Simulator:
    def __init__(self, root, binary, selector):
        self.root, self.binary, self.selector = map(Path,(root,binary,selector))
        self.protocol = json.loads((self.root/'protocol.json').read_text())
        self.ledger = self.root/'attempts'
        self.ledger.mkdir(exist_ok=True)
    def evaluate(self, indices, arm, *, mode='corrected', export=False, refined=False):
        p = self.protocol
        if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(p['deadline_utc']):
            raise RuntimeError('Protocol deadline exhausted')
        for key,path in [('binary_sha256',self.binary),('selector_sha256',self.selector)]:
            if sha(path)!=p[key]:raise RuntimeError('Frozen runtime hash mismatch')
        number = len(list(self.ledger.glob('[0-9]*')))+1
        if number>p['max_simulator_attempts']:raise RuntimeError('Attempt budget exhausted')
        _,variables,deck = render('inverter',list(indices),mode,export,refined)
        deck = deck.replace(str(PROJECT/'tools/sky130_subset.lib.spice'),str(self.selector))
        folder = self.ledger/f'{number:03d}'
        folder.mkdir()
        (folder/'circuit.spice').write_text(deck)
        command = [str(self.binary),'-n','-b','circuit.spice']
        row = {'attempt':number,'arm':arm,'indices':list(indices),'variables':variables,
               'mode':mode,'export':export,'refined':refined,'status':'launch_pending',
               'command':command,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
               'deck_sha256':sha(folder/'circuit.spice'),
               'affinity':sorted(os.sched_getaffinity(0))}
        save(folder/'attempt.json',row) # Debit before invoking a process, including failures.
        def limits():
            resource.setrlimit(resource.RLIMIT_CPU,(15,15))
            resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.monotonic()
        failure = None
        try:
            proc = subprocess.run(command,cwd=folder,env=ENV,capture_output=True,text=True,timeout=20,preexec_fn=limits)
            stdout,stderr,code = proc.stdout,proc.stderr,proc.returncode
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or b''
            if isinstance(stdout,bytes):stdout=stdout.decode(errors='replace')
            stderr,code,failure = '20 second process timeout',None,'timeout'
        except OSError as error:
            stdout,stderr,code,failure = '',str(error),None,'launch_error'
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        (folder/'stdout.log').write_text(stdout)
        (folder/'stderr.log').write_text(stderr)
        def raw(name):
            matches = re.findall(rf'(?m)^\s*{re.escape(name)}\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)',stdout)
            result = float(matches[-1]) if matches else None
            return result if result is not None and math.isfinite(result) else None
        metrics = {}
        for name in ('dc_gain_db','average_delay','dynamic_power'):
            field = 'dynamic_power_timeweighted' if name=='dynamic_power' and mode=='corrected' else name
            value = raw(field)
            metrics[name] = None if value is None else value*float(CFG['metric_post'][name].get('scale',1))
        row.update(score(CFG,metrics))
        diagnostic = stdout+'\n'+stderr
        if failure:status=failure
        elif code!=0:status='process_error'
        elif re.search(r'could not find|can.t open|undefined parameter|cannot find|no such.*model',diagnostic,re.I):status='pdk_or_model_error'
        elif re.search(r'timestep too small|singular matrix|doanalyses.*failed',diagnostic,re.I):status='solver_error'
        elif re.search(r'\berror\b|\bfatal\b|no such vector',diagnostic,re.I) or not row['measurement_valid']:status='measurement_invalid'
        else:status='valid_feasible' if row['feasible'] else 'valid_infeasible'
        if not status.startswith('valid_'):
            row.update(measurement_valid=False,feasible=False,normalized_fom=None,yaml_fom=None,constraint_violation=None)
        row.update(status=status,metrics=metrics,returncode=code,
                   extras={k:raw(k) for k in ('tphl','tplh','static_power_abs','time_mean_power')},
                   wall_seconds=time.monotonic()-start,
                   cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                   peak_rss_kib_upper_bound=after.ru_maxrss)
        save(folder/'attempt.json',row)
        return row

def freeze(root,binary,selector):
    root = Path(root)
    root.mkdir(parents=True,exist_ok=False)
    now = dt.datetime.now(dt.timezone.utc)
    files = [HERE/'bridge.py',HERE/'PROTOCOL.md',HERE/'check.py',HERE/'test_bridge.py',
             PROJECT/'upstream/inverter.yaml',PROJECT/'experiments/optimization_v1/scripts/engine.py',
             PROJECT/'experiments/optimization_v1/scripts/search.py',PROJECT/'april_api_stage/api_controller.py']
    protocol = {'created_utc':now.isoformat(),'deadline_utc':(now+dt.timedelta(hours=2)).isoformat(),
                'seed':11,'circuit':'inverter','backend':'TEST_CONTROLLER_NOT_LLM',
                'api_calls_allowed':False,'max_simulator_attempts':56,'planned_simulator_attempts':53,
                'planned_debit':'3 preflight + 24 test-controller + 24 independent GP control + 2 winner remeasurements',
                'binary_sha256':sha(binary),'selector_sha256':sha(selector),
                'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PROJECT,text=True).strip(),
                'files_sha256':{str(f.relative_to(PROJECT)):sha(f) for f in files},
                'affinity':sorted(os.sched_getaffinity(0)),'threads_per_library':1,
                'cpu_seconds_per_attempt':15,'wall_seconds_per_attempt':20,'memory_bytes_per_attempt':2*1024**3}
    save(root/'protocol.json',protocol)
    version = subprocess.run([str(binary),'--version'],capture_output=True,text=True,check=True)
    (root/'ngspice-version.txt').write_text(version.stdout+version.stderr)
    return Simulator(root,binary,selector)

def verify_frozen(sim):
    for relative,expected in sim.protocol['files_sha256'].items():
        if sha(PROJECT/relative)!=expected:raise RuntimeError('Frozen code/source changed')
    if sorted(os.sched_getaffinity(0))!=list(range(24,32)):
        raise RuntimeError('This APRIL protocol requires CPUs 24-31')

def preflight(sim):
    rows = [sim.evaluate([4,4],'preflight_source',mode='original',export=True),
            sim.evaluate([4,4],'preflight_corrected',export=True),
            sim.evaluate([4,4],'preflight_refined',export=True,refined=True)]
    save(sim.root/'preflight.json',rows)
    if not all(r['measurement_valid'] for r in rows[1:]):
        raise RuntimeError('Corrected/refined preflight failed; inspect logs; no pilot')
    # Independent waveform verification is a required gate before pilot.
    subprocess.run([sys.executable,str(HERE/'check.py'),str(sim.root),'--preflight'],check=True,env=os.environ|ENV)

def choose(method, candidates, history, rng):
    if method=='random' or len(history)<10:
        return candidates[int(rng.integers(len(candidates)))],{'engine':'random' if method=='random' else 'GP_10_point_initialization'}
    return propose_gp(candidates,history,rng)

def run_controller(sim, controller):
    root = sim.root/'test_controller'
    root.mkdir()
    history, domains = [], []
    rng = np.random.default_rng(11)
    def call(stage,understanding=None,domain=None):
        messages = request(stage,history,understanding,domain)
        n = len(list(root.glob('call_*')))+1
        folder = root/f'call_{n:02d}_{stage}'
        folder.mkdir()
        save(folder/'request.json',{'backend':controller.label,'messages':messages})
        try:
            response = controller.call(stage=stage,messages=messages)
            save(folder/'raw_response.json',response)
            validate(stage,response,remaining=24-len(history))
            if stage=='inner_iteration' and response['action']=='search' and response['n_samples']!=12:
                raise ValueError('Fixed pilot requires batches of twelve')
            if stage in ('initial_search_space','outer_regeneration'):
                domain_points(response,[r['indices'] for r in history])
            save(folder/'validated.json',response)
            return response
        except Exception as error:
            save(folder/'error.json',{'type':type(error).__name__,'message':str(error)})
            raise
    cu = call('circuit_understanding')
    initial = call('initial_search_space',cu)
    domain = domain_points(initial)
    for batch in range(2):
        if batch:
            value = call('outer_regeneration',cu,domain)
            domain = domain_points(value,[r['indices'] for r in history])
        domains.append(domain)
        decision = call('inner_iteration',cu,domain)
        if decision['action']=='stop':break
        for _ in range(decision['n_samples']):
            seen = {tuple(r['indices']) for r in history}
            candidates = [p for p in domain if p not in seen]
            point, detail = choose(decision['method'],candidates,history,rng)
            row = sim.evaluate(point,'test_controller')
            row['proposal_detail'] = detail
            history.append(row)
            save(root/'history.json',history)
        save(root/f'feedback_batch_{batch+1}.json',feedback(history,domain))
    save(root/'summary.json',{'backend':controller.label,'model_calls':0,'attempts':len(history),
                             'domain_changed':len(domains)==2 and domains[0]!=domains[1],
                             'valid':sum(r['measurement_valid'] for r in history),
                             'feasible':sum(r['feasible'] for r in history)})
    return history

def run_control(sim):
    # Fresh history; no controller-arm feedback or legacy results are read.
    history, candidates = [],list(itertools.product(range(9),repeat=2))
    rng = np.random.default_rng(11)
    for _ in range(24):
        unseen = [p for p in candidates if p not in {tuple(r['indices']) for r in history}]
        point,detail = choose('bayesian',unseen,history,rng)
        row = sim.evaluate(point,'gp_control')
        row['proposal_detail'] = detail
        history.append(row)
        save(sim.root/'gp_control/history.json',history)
    return history

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase',choices=['preflight','fixture'])
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--selector',type=Path,required=True)
    args = parser.parse_args()
    if args.phase=='preflight':sim=freeze(args.root,args.binary,args.selector)
    else:sim=Simulator(args.root,args.binary,args.selector)
    verify_frozen(sim)
    with threadpool_limits(limits=1):
        if args.phase=='preflight':preflight(sim)
        else:
            if not json.loads((sim.root/'preflight_checks.json').read_text())['passed']:
                raise RuntimeError('Independent preflight required')
            fixture = run_controller(sim,TestController())
            control = run_control(sim)
            for arm,history in [('test_controller',fixture),('gp_control',control)]:
                winner=incumbent(history)
                if winner:sim.evaluate(winner['indices'],arm+'_winner_validation',export=True,refined=True)
            subprocess.run([sys.executable,str(HERE/'check.py'),str(sim.root)],check=True,env=os.environ|ENV)

if __name__=='__main__':main()
