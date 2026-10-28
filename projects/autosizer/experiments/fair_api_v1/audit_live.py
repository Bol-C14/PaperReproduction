"""Read-only independent audit of the new fair pilot; no API or simulator calls."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import math
import sys
from plan import digest
from fair_runtime import PLAN,atomic
PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT/'experiments/bridge_v1'))
from check import independent_metrics,rescore,waveforms

def attempts(root):
    return [(p,json.loads((p/'attempt.json').read_text())) for p in sorted((root/'attempts').glob('[0-9]*'))]

def audit_raw(root,preflight_only=False):
    pairs=attempts(root);checks=[]
    for p,row in pairs:
        assert hashlib.sha256((p/'circuit.spice').read_bytes()).hexdigest()==row['deck_sha256']
        assert row['status']!='launch_pending'
        assert row['affinity']==list(range(24,32))
        assert (p/'stdout.log').exists() and (p/'stderr.log').exists()
        if row['measurement_valid']:
            m=independent_metrics(row,p);fom,feasible=rescore(m)
            assert m==row['metrics'] and math.isclose(fom,row['normalized_fom'],rel_tol=1e-12)
            assert feasible==row['feasible']
            if row['mode']=='corrected' and row['export']:checks.append(waveforms(row,p))
        else:assert row['normalized_fom'] is None
    if preflight_only:assert len(pairs)==3 and len(checks)==2
    return checks

def audit_preflight(root):
    checks=audit_raw(root,True)
    atomic(root/'preflight_checks.json',{'passed':True,'independent_waveforms':checks,'optimizer_observations':False})

def arm_summary(common,fresh):
    allrows=common+fresh;feasible=[r for r in allrows if r['feasible']]
    baseline=[r['normalized_fom'] for r in common if r['feasible']]
    best=max((r['normalized_fom'] for r in feasible),default=None)
    return {'common':len(common),'fresh_attempts':len(fresh),'observations':len(allrows),
            'fresh_unique':len({tuple(r['indices']) for r in fresh}),
            'fresh_valid':sum(r['measurement_valid'] for r in fresh),
            'fresh_feasible':sum(r['feasible'] for r in fresh),
            'feasible_at_initialization':bool(baseline),'baseline_best_feasible':max(baseline,default=None),
            'best_feasible_fom':best,
            'improvement_over_common':None if not baseline or best is None else best-max(baseline)}

def audit(root):
    pairs=attempts(root);rows=[r for _,r in pairs]
    checks=audit_raw(root)
    ledger=json.loads((root/'project_ledger.json').read_text())
    common=json.loads((root/'common.json').read_text())
    assert digest(common)==ledger['common_sha256']
    assert [r['indices'] for r in common]==PLAN['initial_indices']
    assert len(rows)==len(ledger['spice'])<=63
    assert [r['attempt'] for r in rows]==list(range(1,len(rows)+1))
    byid={r['project_attempt_id']:r for r in rows}
    assert len(byid)==len(rows)
    for debit in ledger['spice']:
        r=byid[debit['attempt_id']]
        assert debit['indices']==r['indices'] and debit['status']==r['status']
        assert debit['spawn_confirmed']==r['spawn_confirmed']
    summaries={}
    for arm in ('api_guided','fixed_gp'):
        path=root/(arm+'_history.json');fresh=json.loads(path.read_text()) if path.exists() else []
        assert len({tuple(r['indices']) for r in fresh})==len(fresh)
        assert not {tuple(r['indices']) for r in fresh}&{tuple(r['indices']) for r in common}
        assert len(fresh)==sum(r['kind']=='search' and r['arm']==arm for r in ledger['spice'])
        for r in common+fresh:
            raw=byid[r['attempt_id']]
            assert all(r[k]==raw[k] for k in ('indices','status','metrics','normalized_fom','feasible'))
        summaries[arm]=arm_summary(common,fresh)
    decision_rows=json.loads((root/'decisions.json').read_text())
    for d in decision_rows:
        if d['detail']['engine']=='GP_UCB':
            path=root/(d['arm']+'_history.json');history=common+json.loads(path.read_text())[:d['fresh_ordinal']-1]
            assert d['detail']['training_valid_observations']==sum(r['measurement_valid'] for r in history)
    costs=[];usage=[]
    for api in ledger['api']:
        p=root/'api'/api['attempt_id'];request=json.loads((p/'request.json').read_text())
        context=json.loads(request['messages'][1]['content'])['context']
        if api['stage'] in ('outer_regeneration','inner_second'):
            assert context['remaining_attempts']==12 and context['fresh_attempts_used']==12
            assert len(context['history'])==22
        assert all(r['origin'] in ('common','api_guided') for r in context['history'])
        response=p/'response.json'
        if response.exists():
            u=json.loads(response.read_text()).get('usage',{});usage.append(u)
            if u.get('cost') is not None:costs.append(Decimal(str(u['cost'])))
            else:costs.append(Decimal(api['maximum_token_cost_usd']))
        else:costs.append(Decimal(api['maximum_token_cost_usd']))
    report={'passed':True,'actual_spice_attempts':len(rows),'valid_spice':sum(r['measurement_valid'] for r in rows),
            'api_attempts':len(ledger['api']),'api_cost_accounted_usd':str(sum(costs,Decimal(0))),
            'api_usage':usage,'independent_waveform_checks':checks,'arms':summaries,
            'shared_common_data_exact':True,'preflight_or_control_never_in_guided_prompts':True,
            'matched_budget':all(s['fresh_attempts']==24 for s in summaries.values()),
            'simulator_cpu_seconds':sum(r['cpu_seconds'] for r in rows),
            'simulator_wall_seconds':sum(r['wall_seconds'] for r in rows),
            'limitations':['one circuit/seed; descriptive integration only','API model/config and numerical/measurement substitutions disclosed']}
    assert len(ledger['api'])<=10
    atomic(root/'checks.json',report)
    print(json.dumps({k:report[k] for k in ('passed','actual_spice_attempts','api_attempts','api_cost_accounted_usd','matched_budget','arms')},indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('root',type=Path)
    audit(p.parse_args().root)
