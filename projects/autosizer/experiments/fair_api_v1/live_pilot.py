"""Authorized fair CPU/API pilot. Uses only the shared public Client for network.
Fresh root required. Never loads/prints/copies a key or modifies shared policy.
"""
from pathlib import Path
import argparse
import datetime as dt
from decimal import Decimal
import hashlib
import itertools
import json
import os
import subprocess
import sys
import traceback
import numpy as np
from threadpoolctl import threadpool_limits

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
sys.path.insert(0,str(PROJECT/'experiments/bridge_v1'))
from bridge import Simulator,sha
from fair_runtime import (AttemptLedger,FairBatchRunner,PLAN,CONFIG,build_messages,
                          correction_messages,atomic,BudgetError)
from shared_controller import SharedController
from search import propose_gp
from engine import incumbent


def public_observation(raw,attempt,origin):
    return {'attempt_id':attempt,'origin':origin,
            **{key:raw[key] for key in ('indices','variables','status','measurement_valid','metrics',
                                       'normalized_fom','constraints','feasible','constraint_violation')}}

def domain(value):
    cfg=value['optimization_configuration'];choices=[]
    values=[.84,1.05,1.26,1.47,1.68,1.89,2.1,2.31,2.52]
    for name in ('W_pmos_base','W_nmos_base'):
        if name in cfg['variables_to_optimize']:
            choices.append([values.index(v) for v in cfg['variables_to_optimize'][name]['search_space']])
        else:
            v=cfg['variables_fixed'][name];choices.append([values.index(v['fixed_value'] if isinstance(v,dict) else v)])
    return sorted(itertools.product(*choices))


def freeze(args,shared_module):
    args.root.mkdir(parents=True,exist_ok=False)
    now=dt.datetime.now(dt.timezone.utc)
    files=list(HERE.glob('*.py'))+[HERE/'PROTOCOL.md',HERE/'OPENROUTER_PENDING_CONFIG.json',HERE/'PLAN.json',
          PROJECT/'upstream/inverter.yaml',PROJECT/'experiments/bridge_v1/bridge.py',
          PROJECT/'experiments/optimization_v1/scripts/engine.py',PROJECT/'experiments/optimization_v1/scripts/search.py']
    p={'stage':'fair_api_v1_actual','created_utc':now.isoformat(),'deadline_utc':(now+dt.timedelta(hours=2)).isoformat(),
       'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PROJECT,text=True).strip(),
       'files_sha256':{str(x.relative_to(PROJECT)):sha(x) for x in files},
       'shared_source_sha256':sha(shared_module),'binary_sha256':sha(args.binary),'selector_sha256':sha(args.selector),
       'max_simulator_attempts':63,'model':'google/gemini-2.5-flash','max_api_attempts':10,
       'shared_stage_cumulative_budget_usd':'10.00','project_reservation_ceiling_usd':'3.20',
       'input_reservation_basis':'Official fixed Gemini 2.5 Flash input context ceiling 1048576 per request; not exact input tokenization',
       'input_tokens_reserved_total_max':10485760,'generated_tokens_total_max':7168,
       'seed':11,'common_attempts':10,'fresh_attempts_per_arm':24,
       'affinity':sorted(os.sched_getaffinity(0)),'numerical_threads':1,'spice_serial':True,
       'source_normalization':'(gain_dB/20)/((delay_ps/50)*(dynamic_power_uW/50)); strict clauses all required',
       'substitutions':['OpenRouter standard Google AI Studio route','reasoning explicitly off','JSON output cap and no top_k through this route','corrected paired-edge/time-weighted measurement port','fixed scikit-learn GP-UCB numerical port']}
    if p['affinity']!=list(range(24,32)):raise RuntimeError('Expected CPU24-31 affinity')
    atomic(args.root/'protocol.json',p)
    return Simulator(args.root,args.binary,args.selector)


def run(args):
    # No credential access until public signature/model prerequisites are checked.
    sys.path.insert(0,str(args.shared_module.parent))
    from openrouter_shared import load_config,Client
    import inspect
    if 'request_options' not in inspect.signature(Client.chat).parameters:
        raise RuntimeError('Shared public chat request_options not installed; no request or simulation launched')
    client=Client(load_config()) # Shared loader only; never serialize/print config.
    if client.config.public_settings().get('chat_model')!='google/gemini-2.5-flash':
        raise RuntimeError('Shared configured model differs from frozen pilot')
    sim=freeze(args,args.shared_module)
    ledger=AttemptLedger(args.root/'project_ledger.json')
    controller=SharedController(client,ledger,run_id=args.root.name,token_counter=None,evidence_dir=args.root/'api')
    controller.check_interface()
    rawmap={}
    def measured(point,origin,kind='search',mode='corrected',export=False,refined=False,attempt=None):
        own=attempt or ledger.reserve_spice(kind=kind,indices=point,arm=origin if kind in ('search','validation') else None)
        raw=sim.evaluate(point,origin,mode=mode,export=export,refined=refined)
        raw['project_attempt_id']=own
        raw['spawn_confirmed']=raw['status']!='launch_error'
        atomic(args.root/'attempts'/f"{raw['attempt']:03d}"/'attempt.json',raw)
        rawmap[own]=raw['attempt']
        if attempt is None:ledger.finish_spice(own,status=raw['status'],spawn_confirmed=raw['spawn_confirmed'])
        if attempt is not None:return raw
        row=public_observation(raw,own,'common' if kind=='common' else origin)
        return row
    # All calls here are new, charged measurements. Safety samples are excluded.
    preflight=[measured([4,4],'preflight_source',kind='preflight',mode='original',export=True),
               measured([4,4],'preflight_corrected',kind='preflight',export=True),
               measured([4,4],'preflight_refined',kind='preflight',export=True,refined=True)]
    atomic(args.root/'preflight.json',preflight)
    if not all(r['measurement_valid'] for r in preflight[1:]):raise RuntimeError('Preflight invalid')
    # New independent vectors/units checker, never an optimizer observation.
    from audit_live import audit_preflight
    audit_preflight(args.root)
    common=[measured(p,'common',kind='common') for p in PLAN['initial_indices']]
    ledger.freeze_common(common);atomic(args.root/'common.json',common)
    guided=FairBatchRunner(ledger,'api_guided',common)
    rng=np.random.default_rng(11)
    decisions=[]
    failure=None
    def model(stage,cu=None,points=None):
        messages=build_messages(stage,ledger=ledger,common_rows=common,arm_rows=guided.history,understanding=cu,
                                domain=None if points is None else [list(p) for p in points])
        for trial in range(2):
            try:return controller.call(stage,messages,authorize_live=True)
            except BudgetError:
                last=ledger.data['api'][-1] if ledger.data['api'] else None
                if trial or last is None or last['status']!='schema_invalid':raise
                folder=args.root/'api'/last['attempt_id']
                response=json.loads((folder/'response.json').read_text())
                raw=response['choices'][0]['message']['content']
                error=json.loads((folder/'error.json').read_text())['validation_error']
                messages=correction_messages(messages,raw,error)
    def search_batch(runner,method,points):
        def propose(history):
            seen={tuple(r['indices']) for r in history};candidates=[p for p in points if p not in seen]
            if not candidates:raise RuntimeError('Domain exhausted; no implicit expansion')
            if method=='random':point=candidates[int(rng.integers(len(candidates)))];detail={'engine':'random'}
            else:point,detail=propose_gp(candidates,history,rng)
            decisions.append({'arm':runner.arm,'fresh_ordinal':ledger.used(runner.arm)+1,
                              'indices':list(point),'method':method,'domain':[list(p) for p in points],'detail':detail})
            atomic(args.root/'decisions.json',decisions)
            return point
        runner.run_batch(12,propose=propose,evaluate=lambda p,a:measured(p,runner.arm,attempt=a))
    try:
        cu=model('circuit_understanding')
        initial=model('initial_search_space',cu)
        points=domain(initial)
        decision=model('inner_first',cu,points)
        if decision['action']=='search':
            search_batch(guided,decision['method'],points)
            regenerated=model('outer_regeneration',cu,points)
            points=domain(regenerated)
            second=model('inner_second',cu,points)
            if second['action']=='search':search_batch(guided,second['method'],points)
    except Exception as error:
        failure={'type':type(error).__name__,'status':'guided_arm_stopped','requests_charged':len(ledger.data['api'])}
        atomic(args.root/'guided_failure.json',failure)
        # No exception message or config dump; complete source/error files stay local.
    control=FairBatchRunner(ledger,'fixed_gp',common)
    rng=np.random.default_rng(11) # Same initial RNG state; numerical policy differs only by model decisions.
    for _ in range(2):search_batch(control,'bayesian',list(itertools.product(range(9),repeat=2)))
    for arm,history in [('api_guided',guided.history),('fixed_gp',control.history)]:
        winner=incumbent(common+history)
        if winner:measured(winner['indices'],arm,kind='validation',export=True,refined=True)
    atomic(args.root/'raw_attempt_map.json',rawmap)
    atomic(args.root/'execution_summary.json',{'guided_failure':failure,'api_attempts':len(ledger.data['api']),
          'guided_fresh':ledger.used('api_guided'),'control_fresh':ledger.used('fixed_gp'),
          'common':len(common),'spice_attempts':len(ledger.data['spice']),
          'matched_budget':ledger.used('api_guided')==ledger.used('fixed_gp')==24})
    from audit_live import audit
    audit(args.root)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--selector',type=Path,required=True);parser.add_argument('--shared-module',type=Path,required=True)
    args=parser.parse_args()
    with threadpool_limits(limits=1):run(args)
