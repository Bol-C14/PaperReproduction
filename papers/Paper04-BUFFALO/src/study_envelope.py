#!/usr/bin/env python3
"""Bounded load-domain correction and same-implementation area-delay panel.
Twelve predeclared local STA calls maximum. No target changes or APIs.
"""
import argparse,copy,hashlib,json,time
from pilot import ROOT,library,fixture,flatten
from diagnose_feasibility import shallow,run_case


def main():
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True);a=p.parse_args()
    target=ROOT/'metrics'/'envelope.json'
    if target.exists():raise SystemExit('Existing envelope evidence; refusing rerun/overwrite.')
    path=ROOT/'config'/'envelope_plan.json';plan=json.loads(path.read_text());_,lib=library()
    assert len(plan['cases'])*len(plan['configurations_per_case'])==plan['maximum_new_sta_calls']==12
    rows=[];start=time.perf_counter();calls=0
    for name in plan['cases']:
        for spec in plan['configurations_per_case']:
            f=copy.deepcopy(fixture(name));assert f['required_ps']==plan['required_ps_remains']
            f['output_load_ff']=spec['output_load_ff'];tree=shallow(f,spec['centroid_fraction'])
            for n in flatten(tree):
                if n['id'].startswith('B'):n['cell']=spec['buffer_cell']
            assert calls<12
            calls+=1 # count every attempted invocation, including subprocess exceptions
            try:r=run_case(f,spec['label'],tree,a.engine,ROOT/'vendor'/'asap7.lib',lib)
            except Exception as e:
                r={'net':name,'configuration':spec['label'],'status':'CALL_OR_PREPARATION_ERROR','error_type':type(e).__name__,'error':str(e),'sta_attempts_budget_charged':1}
            r['output_load_ff']=spec['output_load_ff'];r['buffer_cell']=spec['buffer_cell'];r['centroid_fraction']=spec['centroid_fraction']
            r['required_ps']=f['required_ps'];r['purpose']=spec['purpose']
            out=ROOT/'runs'/'feasibility'/name/spec['label'];out.mkdir(parents=True,exist_ok=True)
            (out/'fixture.json').write_text(json.dumps(f,indent=2)+'\n');(out/'panel_result.json').write_text(json.dumps(r,indent=2)+'\n')
            rows.append(r);print(json.dumps(r),flush=True)
    # Nondominance only within identical net and boundary load.
    for r in rows:
        r['pareto_eligible']=r['status'] in ['TIMING_VIOLATION','TIMING_FEASIBLE_UNDER_DECLARED_MODEL']
        peers=[q for q in rows if q['net']==r['net'] and q['output_load_ff']==r['output_load_ff'] and q['status'] in ['TIMING_VIOLATION','TIMING_FEASIBLE_UNDER_DECLARED_MODEL']]
        r['nondominated_within_panel']=r['pareto_eligible'] and not any(q['buffer_area']<=r['buffer_area'] and q['max_arrival_ps']<=r['max_arrival_ps'] and (q['buffer_area']<r['buffer_area'] or q['max_arrival_ps']<r['max_arrival_ps']) for q in peers)
        if r['pareto_eligible']:
            r['fixed_implementation_min_required_ps']=r['max_arrival_ps']
            r['counterfactual_endpoint_feasible']={str(t):r['max_arrival_ps']<=t for t in plan['counterfactual_required_grid_ps']}
    s={'plan_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'new_configurations':len(rows),'sta_attempt_budget_charged':calls,
       'successful_engine_results':sum('returncode' in r and r['returncode']==0 for r in rows),
       'call_or_preparation_errors':sum(r['status']=='CALL_OR_PREPARATION_ERROR' for r in rows),
       'tool_or_observation_errors':sum(r['status'] in ['TOOL_OR_OBSERVATION_ERROR','CONSTRAINT_OR_METRIC_ERROR','PATH_ACCOUNTING_ERROR'] for r in rows),
       'sta_wall_seconds':sum(r.get('sta_wall_seconds',0) for r in rows),'total_wall_seconds':time.perf_counter()-start,
       'api_calls':0,'training_steps':0,'physical_runs':0,'actual_target_ps':80,'rows':rows}
    target.write_text(json.dumps(s,indent=2)+'\n')

if __name__=='__main__':main()
