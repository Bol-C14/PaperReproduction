"""Offline fair-pilot plan and accounting checks. No simulator/API imports or runner."""
import copy
import hashlib
import itertools
import json
import math
import random
import platform
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
DOMAIN = list(itertools.product(range(9), repeat=2))

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def make_plan(seed=11):
    initial = random.Random(seed).sample(DOMAIN,10)
    return {'status':'DRAFT_NOT_EXECUTION_AUTHORIZATION','api_authorized':False,
            'task':'inverter','seed':seed,'sampling':'random.Random(seed).sample(full lexicographic 81-point grid,10); frozen literal indices are authoritative, do not regenerate at runtime',
            'plan_generator_python':platform.python_version(),
            'source_yaml_sha256':hashlib.sha256((PROJECT/'upstream/inverter.yaml').read_bytes()).hexdigest(),
            'initial_domain':[list(p) for p in DOMAIN],'initial_indices':[list(p) for p in initial],
            'common_attempt_budget':10,'fresh_attempt_budget_per_arm':24,'observation_budget_per_arm':34,
            'arms':['api_guided','fixed_gp'],'physical_search_attempt_budget':58,
            'preflight_attempt_budget':3,'winner_validation_attempt_budget':2,'physical_stage_attempt_cap':63,
            'api_requests_nominal':5,'api_requests_max':10,'api_input_tokens_max':81920,'api_output_tokens_max':7168,
            'api_feedback_observations_max':22,
            'api_label':'PENDING_EXACT_SERVICE_MODEL_TOKENIZER_AND_SPEND_AUTHORIZATION',
            'model_guidance_is_treatment':'domain/subset and random-vs-fixed-GP decisions after identical initialization; no GP/kernel/metric/budget differences',
            'early_stop_or_failure':'honor stop; no filler or replacement. Unequal completed budgets invalidate matched full-budget comparison.'}

def fork_observations(rows, plan=None):
    if len(rows)!=10 or len({tuple(r['indices']) for r in rows})!=10:
        raise ValueError('Ten distinct common attempts required')
    expected = (make_plan() if plan is None else plan)['initial_indices']
    if [r['indices'] for r in rows]!=expected:
        raise ValueError('Common point ordering differs from the frozen plan')
    if any(r.get('status')=='launch_pending' for r in rows):
        raise ValueError('Unresolved attempt cannot be shared')
    # Equal immutable JSON source; separate deep copies prevent cross-arm mutation.
    frozen = json.loads(json.dumps(rows,sort_keys=True,allow_nan=False))
    return {'sha256':digest(frozen),'api_guided':copy.deepcopy(frozen),'fixed_gp':copy.deepcopy(frozen)}

def validate_launch_balance(common, guided, control):
    """Only a full matched search receives passed=True; preflight/validation separate."""
    fork_observations(common)
    for name,rows,count in [('common',common,10),('api_guided',guided,24),('fixed_gp',control,24)]:
        if len(rows)!=count:raise ValueError(name+' attempted-launch count mismatch')
        if any(tuple(r['indices']) not in DOMAIN for r in rows):raise ValueError(name+' illegal point')
        if len({tuple(r['indices']) for r in rows})!=count:raise ValueError(name+' duplicate points')
        if any(not r.get('spawn_confirmed') for r in rows):raise ValueError(name+' actual process launch not confirmed')
        if any(r.get('status')=='launch_pending' for r in rows):raise ValueError(name+' unresolved process outcome')
    seen={tuple(r['indices']) for r in common}
    if any(tuple(r['indices']) in seen for r in guided+control):
        raise ValueError('An arm repeated a common point')
    # Cross-arm coincidences are allowed but must be independently resimulated.
    for key in ('process_id','attempt_id'):
        values=[r[key] for r in common+guided+control]
        if len(set(values))!=58:raise ValueError('Shared/reused '+key+' in actual launch accounting')
    return {'passed':True,'common_actual_launches':10,'fresh_actual_launches_per_arm':24,
            'total_physical_search_launches':58,'observations_per_arm':34,
            'shared_common_launches_counted_once':True}

def independent_parse(stdout, corrected=True):
    def number(name):
        values=re.findall(rf'(?mi)^\s*{re.escape(name)}\s*=\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)',stdout)
        if not values:raise ValueError('Missing metric '+name)
        value=float(values[-1])
        if not math.isfinite(value):raise ValueError('Nonfinite '+name)
        return value
    return {'dc_gain_db':number('dc_gain_db'),
            'average_delay':number('average_delay')*1e12,
            'dynamic_power':number('dynamic_power_timeweighted' if corrected else 'dynamic_power')*1e6}

def independent_score(metrics):
    if set(metrics)!=set(('dc_gain_db','average_delay','dynamic_power')):
        raise ValueError('Exactly three physical measurements required')
    if any(type(v) not in (float,int) or not math.isfinite(v) for v in metrics.values()):
        raise ValueError('Finite physical measurements required')
    gain,delay,power=(metrics[k] for k in ('dc_gain_db','average_delay','dynamic_power'))
    if delay<=0 or power<=0:raise ValueError('Positive delay/power required')
    fom=(gain/20)/((delay/50)*(power/50))
    return {'normalized_fom':fom,'feasible':fom>1 and gain>20 and delay<50 and power<50,
            'constraints':{'fom':fom>1,'dc_gain_db':gain>20,'average_delay':delay<50,'dynamic_power':power<50}}

if __name__=='__main__':
    print(json.dumps(make_plan(),indent=2))
