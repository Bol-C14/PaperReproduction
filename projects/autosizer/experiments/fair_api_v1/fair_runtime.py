"""Fair budget/builder and injected CPU runner. No network transport or live CLI.

Only new per-arm attempted launches debit that arm's SPICE budget. Shared data,
API attempts and output/history rows are separate concepts. Journals are serial.
"""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import yaml
from plan import PROJECT, DOMAIN, digest

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE/'PLAN.json').read_text())
CONFIG = json.loads((HERE/'OPENROUTER_PENDING_CONFIG.json').read_text())
CAPS = CONFIG['caps']
STAGES = tuple(CAPS['output_per_stage'])

class BudgetError(RuntimeError):pass
class InputLimitExceeded(BudgetError):pass
class TokenCounterRequired(BudgetError):pass

def atomic(path,value):
    path=Path(path)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)

class AttemptLedger:
    """Persist debit before any evaluator/transport invocation; never refund failures."""
    def __init__(self,path):
        self.path=Path(path)
        self.data=json.loads(self.path.read_text()) if self.path.exists() else {'spice':[],'api':[]}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self._save()
    def _save(self):atomic(self.path,self.data)
    def used(self,arm):
        if arm not in PLAN['arms']:raise ValueError('Unknown arm')
        return sum(r['kind']=='search' and r['arm']==arm for r in self.data['spice'])
    def remaining(self,arm):return PLAN['fresh_attempt_budget_per_arm']-self.used(arm)
    def freeze_common(self,rows):
        if [r['indices'] for r in rows]!=PLAN['initial_indices']:
            raise ValueError('Frozen common point ordering differs from plan')
        recorded={r['attempt_id']:r for r in self.data['spice']}
        if len({r['attempt_id'] for r in rows})!=10:raise ValueError('Ten common attempt IDs required')
        for row in rows:
            debit=recorded.get(row['attempt_id'])
            if (debit is None or debit['kind']!='common' or debit['indices']!=row['indices']
                or debit['status']=='launch_pending' or debit['status']!=row['status'] or row['origin']!='common'):
                raise ValueError('Common observation does not match completed common debit')
        fingerprint=digest(rows)
        if self.data.get('common_sha256') is not None:
            if self.data['common_sha256']!=fingerprint:raise ValueError('Shared common observations changed')
            return fingerprint
        if any(r['kind']=='search' for r in self.data['spice']):
            raise ValueError('Freeze common observations before either arm begins')
        self.data['common_sha256']=fingerprint;self._save();return fingerprint
    def reserve_spice(self,*,kind,indices,arm=None,retry_of=None):
        rows=self.data['spice']
        if tuple(indices) not in DOMAIN:raise ValueError('Illegal released grid point')
        if len(rows)>=PLAN['physical_stage_attempt_cap']:raise BudgetError('Stage SPICE cap')
        if kind=='search':
            if self.remaining(arm)<=0:raise BudgetError('Current arm SPICE cap')
        elif kind in ('preflight','common','validation'):
            limit={'preflight':3,'common':10,'validation':2}[kind]
            if sum(r['kind']==kind for r in rows)>=limit:raise BudgetError(kind+' SPICE cap')
            if kind=='validation':
                if arm not in PLAN['arms']:raise ValueError('Validation arm required')
                if any(r['kind']==kind and r['arm']==arm for r in rows):raise BudgetError('One winner validation per arm')
            elif arm is not None:raise ValueError('Shared phases have no arm')
        else:raise ValueError('Unknown simulation phase')
        if kind!='preflight' and retry_of is None and any(r['indices']==list(indices) and ((r['kind']==kind and r['arm']==arm) or (kind=='search' and r['kind']=='common')) for r in rows):
            raise ValueError('Repeated point requires explicit charged retry; normal proposals must be unseen')
        if retry_of is not None:
            previous=next((r for r in rows if r['attempt_id']==retry_of),None)
            if previous is None or previous['kind']!=kind or previous['arm']!=arm or previous['indices']!=list(indices):
                raise ValueError('Retry must reference same phase/arm/point')
            if previous['status']=='launch_pending' or previous['status'].startswith('valid_'):
                raise ValueError('Do not retry unresolved or valid attempts')
        row={'attempt_id':f'spice_{len(rows)+1:04d}','kind':kind,'arm':arm,'indices':list(indices),
             'retry_of':retry_of,'status':'launch_pending','spawn_confirmed':False}
        rows.append(row);self._save()
        return row['attempt_id']
    def finish_spice(self,attempt_id,*,status,spawn_confirmed):
        row=next(r for r in self.data['spice'] if r['attempt_id']==attempt_id)
        if row['status']!='launch_pending':raise BudgetError('Outcome already recorded')
        if status=='launch_pending' or type(spawn_confirmed) is not bool:raise ValueError('Final process outcome required')
        row.update(status=status,spawn_confirmed=spawn_confirmed);self._save()
    def reserve_api(self,stage,check):
        """Called by a future authorized transport immediately before a single attempt.
        This method alone never transmits. A local rejected request is not an API call.
        """
        if stage not in STAGES:raise ValueError('Unknown model-decision stage')
        if not check.get('ready_for_authorized_transport'):raise TokenCounterRequired('Token gate not certified')
        rows=self.data['api'];output=CAPS['output_per_stage'][stage]
        if any(r['status'] in ('attempt_pending','provider_or_usage_mismatch') for r in rows):
            raise BudgetError('Unresolved/policy-mismatched API attempt requires reconciliation')
        if len(rows)>=10 or sum(r['stage']==stage for r in rows)>=2:raise BudgetError('API attempt cap')
        tokens=check['input_tokens_upper_bound']
        if type(tokens) is not int or not 0<tokens<=CAPS['input_chat_tokens_per_request']:raise InputLimitExceeded('Invalid certified input bound')
        if sum(r['input_tokens_reserved'] for r in rows)+tokens>CAPS['input_chat_tokens_total']:raise BudgetError('Total input cap')
        if sum(r['output_tokens_reserved'] for r in rows)+output>7168:raise BudgetError('Total generated cap')
        cost=(Decimal(tokens)*Decimal('0.30')+Decimal(output)*Decimal('2.50'))/1000000
        reservation=Decimal('.32')
        if sum((Decimal(r['maximum_token_cost_usd']) for r in rows),Decimal(0))+reservation>Decimal(CAPS['proposed_token_spend_ceiling_usd']):
            raise BudgetError('Proposed token spend cap')
        row={'attempt_id':f'api_{len(rows)+1:02d}','stage':stage,'status':'attempt_pending',
             'input_tokens_reserved':tokens,'output_tokens_reserved':output,
             'maximum_token_cost_usd':str(reservation),'pricing_formula_bound_usd':str(cost),'request_sha256':check['messages_sha256']}
        rows.append(row);self._save();return row['attempt_id']
    def finish_api(self,attempt_id,status):
        row=next(r for r in self.data['api'] if r['attempt_id']==attempt_id)
        if row['status']!='attempt_pending':raise BudgetError('API outcome already recorded')
        if status not in ('valid','schema_invalid','transport_failure','timeout','provider_or_usage_mismatch'):
            raise ValueError('Unknown API outcome')
        row['status']=status;self._save()

PUBLIC_ROW_FIELDS=('attempt_id','origin','indices','variables','status','measurement_valid',
                   'metrics','normalized_fom','constraints','feasible','constraint_violation')

def project_row(row):
    if set(PUBLIC_ROW_FIELDS)-set(row):raise ValueError('Incomplete public observation')
    return {k:copy.deepcopy(row[k]) for k in PUBLIC_ROW_FIELDS}

def build_messages(stage,*,ledger,common_rows,arm_rows,understanding=None,domain=None):
    if stage not in STAGES:raise ValueError('Unknown stage')
    if [r['indices'] for r in common_rows]!=PLAN['initial_indices']:
        raise ValueError('Frozen common data/ordering mismatch')
    if ledger.data.get('common_sha256')!=digest(common_rows):
        raise ValueError('Exact shared common observations must be frozen first')
    recorded={r['attempt_id']:r for r in ledger.data['spice']}
    all_rows=common_rows+arm_rows
    if len({r['attempt_id'] for r in all_rows})!=len(all_rows):raise ValueError('Duplicate observations')
    for row in all_rows:
        debit=recorded.get(row['attempt_id'])
        expected='common' if row['origin']=='common' else 'search'
        if debit is None or debit['kind']!=expected or debit['indices']!=row['indices']:
            raise ValueError('Observation does not match charged attempt')
        if expected=='search' and (debit['arm']!='api_guided' or row['origin']!='api_guided'):
            raise ValueError('Control/private data excluded')
        if debit['status']=='launch_pending' or debit['status']!=row['status']:
            raise ValueError('Unresolved or mismatched observation')
    if any(r['origin']!='common' for r in common_rows) or any(r['origin']!='api_guided' for r in arm_rows):
        raise ValueError('Incorrect observation pool')
    if ledger.used('api_guided')!=len(arm_rows):
        # Missing failure/pending rows cannot silently disappear from scientific history.
        raise ValueError('Every charged fresh attempt must have one completed public row')
    if stage in ('outer_regeneration','inner_second') and ledger.used('api_guided')!=12:
        raise ValueError('Reflection/second decision requires exactly twelve fresh attempts')
    if stage in ('circuit_understanding','initial_search_space','inner_first') and ledger.used('api_guided')!=0:
        raise ValueError('Initial model stages must precede fresh search')
    if stage!='circuit_understanding' and not isinstance(understanding,dict):raise ValueError('Actual understanding required')
    source=PROJECT/'upstream/inverter.yaml'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=PLAN['source_yaml_sha256']:
        raise ValueError('Frozen public source changed')
    cfg=yaml.safe_load(source.read_text())
    context={k:cfg[k] for k in ('ota_subckt_template','params','width_scales','W_values','metric_post','user_specs_metric')}
    context['testbench_template']=cfg['testbench_template'].replace('{pdk_lib_path}','PUBLIC_SKY130_TT_SELECTOR')
    context.update(measurement_port='27 C; paired opposite output edges at 0.9 V; 0..4 ns integral mean supply power minus static 10..90 ps mean',
                   normalization='(gain_dB/20)/((delay_ps/50)*(power_uW/50)); all strict clauses required',
                   units={'dc_gain_db':'dB','average_delay':'ps','dynamic_power':'uW'},
                   initial_domain=PLAN['initial_domain'],domain=domain,
                   understanding=understanding,
                   history=[] if stage=='circuit_understanding' else [project_row(r) for r in all_rows],
                   common_observations=10,fresh_attempts_used=ledger.used('api_guided'),
                   remaining_attempts=ledger.remaining('api_guided'),batch_attempts=12,
                   gp_port='Common ten-point initialization already consumed; no extra warmup. Indices/8; normalized y; fixed Constant(1)*Matern(nu=2.5,length=.35)+WhiteKernel(1e-6); UCB mean+2sd; invalid excluded; random if <3 valid.')
    instructions={
        'circuit_understanding':'Return circuit_topology_overview, optimization_variables_mapping, optimization_variables_impact, variable_interactions, key_insights_for_optimization as nonempty JSON fields; use public topology only.',
        'initial_search_space':'Return optimization_configuration with variables_to_optimize {name:{search_space:[released values]}}, variables_fixed {name:{fixed_value:released value}}, reasoning, search_space_summary. Cover each variable once; >=12 unseen combinations.',
        'inner_first':'Return {action:search|stop,method:random|bayesian,n_samples:12,parameters:{},reasoning:nonempty string}. Stop is honored; exact numerical port and batch cap fixed.',
        'outer_regeneration':'Reflect on actual common+fresh measurements. Return initial domain schema with >=12 unseen combinations and honest change/no-change reasoning. Preserve all observations; no invented results.',
        'inner_second':'Return same inner decision schema, n_samples:12 for search or stop; twelve fresh attempts remain, independent of ten common observations.'}
    messages=[{'role':'system','content':'AutoSizer fair API pilot. Return exactly one JSON object. No invented measurements or access to control/oracle results.'},
              {'role':'user','content':json.dumps({'stage':stage,'instruction':instructions[stage],'context':context},ensure_ascii=False,separators=(',',':'))}]
    if re.search(r'/(?:home|Users)/[^\s"\x27]+',json.dumps(messages)):
        raise ValueError('Runtime/private paths cannot enter model messages')
    return messages

def correction_messages(messages,raw_response,validation_error):
    if not isinstance(raw_response,str) or not isinstance(validation_error,str):raise ValueError('Exact raw correction text required')
    # Keep the complete invalid output and exact local schema error; never truncate history.
    return copy.deepcopy(messages)+[{'role':'assistant','content':raw_response},
                                    {'role':'user','content':'Correct JSON/schema/domain error: '+validation_error}]

def check_input(messages,*,token_counter=None):
    encoded=json.dumps(messages,ensure_ascii=False).encode()
    report={'messages_sha256':digest(messages),'serialized_messages_bytes':len(encoded),
            'ready_for_authorized_transport':False,'input_tokens_upper_bound':None}
    if len(encoded)>CAPS['serialized_messages_bytes']:raise InputLimitExceeded('Full serialized request exceeds frozen byte cap; scientific context retained, not truncated')
    if token_counter is None:
        # Fixed model and no fallback: accepted input including framing cannot
        # exceed its official context capacity. Reserve that whole capacity.
        # This deliberately overestimates usage instead of estimating bytes/4.
        certificate={'model':'google/gemini-2.5-flash','framing_included':True,
                     'certified_upper_bound':True,'tokens':CAPS['input_chat_tokens_per_request'],
                     'counter_id':'OFFICIAL_MODEL_CONTEXT_CEILING_NOT_EXACT_TOKENIZATION'}
    else:certificate=token_counter(messages)
    if (not isinstance(certificate,dict) or certificate.get('model')!='google/gemini-2.5-flash'
        or certificate.get('framing_included') is not True or certificate.get('certified_upper_bound') is not True):
        raise TokenCounterRequired('Counter must certify selected-model chat framing and conservative upper bound')
    bound=certificate.get('tokens')
    if type(bound) is not int or not 0<bound<=CAPS['input_chat_tokens_per_request']:
        raise InputLimitExceeded('Full request upper bound exceeds frozen model-context ceiling or is invalid; no context truncated')
    report.update(ready_for_authorized_transport=True,input_tokens_upper_bound=bound,
                  counter_id=certificate.get('counter_id','unspecified'),
                  admission_basis='official_context_envelope' if token_counter is None else 'supplied_upper_bound')
    return report

def pending_payload(stage,messages,*,token_counter=None):
    if stage not in STAGES:raise ValueError('Unknown stage')
    check=check_input(messages,token_counter=token_counter)
    body=copy.deepcopy(CONFIG['request_template'])
    body.update(messages=copy.deepcopy(messages),max_tokens=CAPS['output_per_stage'][stage])
    return {'execution_enabled':False,'authorization':CONFIG['authorization'],'body':body,'input_check':check}

class FairBatchRunner:
    """Injected evaluator only; no default subprocess/API implementation or CLI.
    evaluate(point,attempt_id) must return process outcome and public metrics.
    Exceptions remain charged; there is no automatic retry or failure replacement.
    """
    def __init__(self,ledger,arm,common_rows):
        if ledger.data.get('common_sha256')!=digest(common_rows):
            raise ValueError('Runner must consume the frozen exact common dataset')
        self.ledger,self.arm,self.common_rows=ledger,arm,copy.deepcopy(common_rows)
        history_path=ledger.path.parent/(arm+'_history.json')
        self.history=json.loads(history_path.read_text()) if history_path.exists() else []
        if ledger.used(arm)!=len(self.history):
            raise BudgetError('Unresolved or missing charged history; reconcile before resuming')
    def run_batch(self,count,*,propose,evaluate):
        if type(count) is not int or count<1 or count>self.ledger.remaining(self.arm):
            raise BudgetError('Batch exceeds current arm remaining attempts')
        for _ in range(count):
            point=propose(copy.deepcopy(self.common_rows+self.history))
            seen={tuple(r['indices']) for r in self.common_rows+self.history}
            if tuple(point) in seen:raise ValueError('Proposal repeats observed point; no launch')
            attempt=self.ledger.reserve_spice(kind='search',arm=self.arm,indices=point)
            try:
                result=evaluate(point,attempt)
                status=result['status'];spawn=result['spawn_confirmed']
                required=set(PUBLIC_ROW_FIELDS)-set(('attempt_id','origin','indices'))
                if not required<=set(result):raise ValueError('Incomplete evaluator outcome')
            except Exception as error:
                # Outcome may be uncertain: the debit stays, no fake observation or retry.
                atomic(self.ledger.path.parent/(attempt+'_error.json'),{'type':type(error).__name__,'status':'outcome_uncertain','charged':True})
                raise BudgetError('Evaluator exception: attempt remains charged/pending; reconcile before continuing') from error
            self.ledger.finish_spice(attempt,status=status,spawn_confirmed=spawn)
            row={'attempt_id':attempt,'origin':self.arm,'indices':list(point),
                 **{k:result[k] for k in PUBLIC_ROW_FIELDS if k not in ('attempt_id','origin','indices')}}
            self.history.append(row)
            atomic(self.ledger.path.parent/(self.arm+'_history.json'),self.history)
        return copy.deepcopy(self.history)
