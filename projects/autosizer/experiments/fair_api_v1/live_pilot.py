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
import shutil
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
    files=list(HERE.glob('*.py'))+[HERE/'SCHEMA_REPAIR_CONTINUATION.md',HERE/'COST_ENVELOPE_PROTOCOL.md',HERE/'PROTOCOL.md',HERE/'OPENROUTER_PENDING_CONFIG.json',HERE/'PLAN.json',
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
    if getattr(args,'resume_from',None):
        old=json.loads((args.resume_from/'protocol.json').read_text())
        for f in ('upstream/inverter.yaml','experiments/bridge_v1/bridge.py','experiments/optimization_v1/scripts/engine.py','experiments/optimization_v1/scripts/search.py'):
            if old['files_sha256'][f]!=sha(PROJECT/f):raise RuntimeError('Physical/numerical source changed; cannot carry observations')
        if old['binary_sha256']!=p['binary_sha256'] or old['selector_sha256']!=p['selector_sha256']:raise RuntimeError('Runtime changed; cannot carry observations')
        carried_ledger=json.loads((args.resume_from/'project_ledger.json').read_text())
        used=sum(r['kind']=='search' and r['arm']=='api_guided' for r in carried_ledger['spice'])
        if used not in (0,12):raise RuntimeError('Only a stopped0/12-attempt guided arm can be continued; do not repeat completed work')
        carried_api=len(carried_ledger['api'])+carried_ledger.get('carried_api_attempts',0)
        p.update(max_simulator_attempts=len(carried_ledger['spice'])+(24-used)+1,continuation_of=args.resume_from.name,source_protocol_sha256=sha(args.resume_from/'protocol.json'),
                 carried_spice_attempts=len(carried_ledger['spice']),carried_api_attempts=carried_api,max_new_api_attempts=10-carried_api,
                 revision='Explicit allowed-variable schema correction; failed phase intact; carry common/control data without remeasurement; prior guided winner validation becomes a charged diagnostic')
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
    continuing=bool(getattr(args,'resume_from',None))
    if continuing:
        old=args.resume_from
        previous=json.loads((old/'project_ledger.json').read_text())
        if (sum(r['kind']=='search' and r['arm']=='api_guided' for r in previous['spice']) not in (0,12) or any(r['status']=='attempt_pending' for r in previous['api'])):
            raise RuntimeError('Continuation state differs; do not duplicate unknown work')
        carried=json.loads(json.dumps(previous));carried['api']=[]
        carried['carried_api_attempts']=len(previous['api'])+previous.get('carried_api_attempts',0)
        used=sum(r['kind']=='search' and r['arm']=='api_guided' for r in previous['spice'])
        carried['physical_spice_cap']=len(previous['spice'])+(24-used)+1
        carried['prior_api_cost_usd']=json.loads((old/'checks.json').read_text())['api_cost_accounted_usd']
        for row in carried['spice']:
            if row['kind']=='validation' and row['arm']=='api_guided':
                row.update(kind='failed_phase_diagnostic',source_kind='validation')
        atomic(args.root/'project_ledger.json',carried)
        for name in ('attempts','api'):
            shutil.copytree(old/name,args.root/('prior_api' if name=='api' else name),dirs_exist_ok=True)
        for name in ('common.json','fixed_gp_history.json','api_guided_history.json','preflight.json','preflight_checks.json','raw_attempt_map.json','decisions.json'):
            if (old/name).exists():shutil.copy2(old/name,args.root/name)
        atomic(args.root/'carry_forward_manifest.json',{'source_run':old.name,
             'files':{str(p.relative_to(old)):sha(p) for p in sorted(old.rglob('*')) if p.is_file()},
             'unchanged_physical_measurements':True,'no_prior_control_data_in_model_prompts':True})
    ledger=AttemptLedger(args.root/'project_ledger.json')
    controller=SharedController(client,ledger,run_id=args.root.name,token_counter=None,evidence_dir=args.root/'api')
    controller.check_interface()
    rawmap=json.loads((args.root/'raw_attempt_map.json').read_text()) if continuing else {}
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
    if continuing:
        common=json.loads((args.root/'common.json').read_text())
        ledger.freeze_common(common)
    else:
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
    starting_guided=len(guided.history)
    rng=np.random.default_rng(11)
    decisions=json.loads((args.root/'decisions.json').read_text()) if continuing else []
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
        if continuing:
            prior=getattr(args,'understanding_response',None) or (args.root/'prior_api/api_01/response.json')
            if getattr(args,'understanding_response',None):
                shutil.copy2(prior,args.root/'understanding_original_response.json')
                prior=args.root/'understanding_original_response.json'
            cu=json.loads(json.loads(prior.read_text())['choices'][0]['message']['content'])
            atomic(args.root/'understanding_provenance.json',{'source':str(prior.relative_to(args.root)),'source_sha256':sha(prior),'actual_online_model_output':True,'synthetic':False})
        else:cu=model('circuit_understanding')
        if len(guided.history)==0:
            initial=model('initial_search_space',cu)
            points=domain(initial)
            decision=model('inner_first',cu,points)
            if decision['action']=='search':search_batch(guided,decision['method'],points)
        else:
            points=[tuple(p) for p in next(d for d in reversed(decisions) if d['arm']=='api_guided')['domain']]
        if len(guided.history)==12:
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
    if not continuing:
        for _ in range(2):search_batch(control,'bayesian',list(itertools.product(range(9),repeat=2)))
    for arm,history in [('api_guided',guided.history),('fixed_gp',control.history)]:
        if continuing and arm=='api_guided' and len(history)==starting_guided:continue
        if continuing and arm=='fixed_gp':continue # Its actual refined winner measurement is carried unchanged.
        winner=incumbent(common+history)
        if winner:measured(winner['indices'],arm,kind='validation',export=True,refined=True)
    atomic(args.root/'raw_attempt_map.json',rawmap)
    atomic(args.root/'execution_summary.json',{'guided_failure':failure,'api_attempts':len(ledger.data['api'])+ledger.data.get('carried_api_attempts',0),'new_api_attempts':len(ledger.data['api']),
          'guided_fresh':ledger.used('api_guided'),'control_fresh':ledger.used('fixed_gp'),
          'common':len(common),'spice_attempts':len(ledger.data['spice']),
          'matched_budget':ledger.used('api_guided')==ledger.used('fixed_gp')==24})
    from audit_live import audit
    audit(args.root)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--resume-from',type=Path);parser.add_argument('--understanding-response',type=Path);parser.add_argument('--selector',type=Path,required=True);parser.add_argument('--shared-module',type=Path,required=True)
    args=parser.parse_args()
    with threadpool_limits(limits=1):run(args)
