#!/usr/bin/env python3
"""Exactly three nets x three predeclared configurations; actual local STA.
No training, model APIs, sweep, retry, target relaxation or driver resizing.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import time
from pilot import ROOT, CELLS, decode, emit, encode, fixture, flatten, library, timing_metrics, validate


def shallow(f, fraction):
    sinks=sorted(copy.deepcopy(f['sinks']),key=lambda n:(n['y'],n['x']))
    groups=[sinks[i:i+f['max_fanout']] for i in range(0,len(sinks),f['max_fanout'])]
    children=[]
    for i,group in enumerate(groups):
        cx=statistics.mean(n['x'] for n in group);cy=statistics.mean(n['y'] for n in group)
        children.append({'id':f'B{i}','cell':CELLS[2],
            'x':round(f['driver']['x']+fraction*(cx-f['driver']['x'])),
            'y':round(f['driver']['y']+fraction*(cy-f['driver']['y'])), 'children':group})
    return dict(f['driver'],children=children)


def run_case(f, label, tree, engine, libpath, lib):
    out=ROOT/'runs'/'feasibility'/f['name']/label;out.mkdir(parents=True,exist_ok=False)
    nodes=flatten(tree);seq=encode(tree);fixed={n['id']:n for n in [f['driver']]+f['sinks']}
    assert decode(seq,fixed)==tree
    (out/'sequence.json').write_text(json.dumps(seq,indent=2)+'\n')
    (out/'decoded_tree.json').write_text(json.dumps(tree,indent=2)+'\n')
    errors=validate(tree,f,lib)
    assert not errors, (f['name'],label,errors)  # predeclared legal alternatives only
    ids=[n['id'] for n in nodes]
    assert len(set(ids))==len(ids)
    assert sum(len(n.get('children',[])) for n in nodes)==len(nodes)-1
    queries,wirelength=emit(tree,f,out,libpath)
    commands=(out/'sta.conf').read_text().splitlines()[:-2]
    for n in nodes:
        for tr in ['rise','fall']:
            for kind,pin,cmd in [('input_slew',n['id']+':A','report_slew'),('input_arrival',n['id']+':A','report_at'),('cell_output_arrival',n['id']+':Y','report_at')]:
                queries.append((kind,pin,tr));commands.append(f'{cmd} -pin {pin} -max -{tr}')
    for i in range(len(f['sinks'])):
        for tr in ['rise','fall']:
            for kind,cmd in [('required','report_rat'),('slack','report_slack')]:
                queries.append((kind,f'y{i}',tr));commands.append(f'{cmd} -pin y{i} -max -{tr}')
    commands+=['report_timing -num_paths 1','exit']
    (out/'sta.conf').write_text('\n'.join(commands)+'\n')
    start=time.perf_counter()
    p=subprocess.run([engine,'-q','-i',str(out/'sta.conf'),'--log',str(out/'engine.log')],capture_output=True,text=True,timeout=30)
    seconds=time.perf_counter()-start
    (out/'stdout.txt').write_text(p.stdout);(out/'stderr.txt').write_text(p.stderr)
    vals=[float(x) for x in p.stdout.splitlines() if re.fullmatch(r'\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\s*',x)]
    log=(out/'engine.log').read_text()
    tool_errors=[line for line in log.splitlines() if re.match(r'^E\s',line)]
    result={'net':f['name'],'configuration':label,'sta_calls':1,'sta_wall_seconds':seconds,
            'connectivity_errors':[], 'library_errors':[], 'geometric_or_electrical_errors':errors,
            'tool_errors':tool_errors,'returncode':p.returncode,
            'query_count':len(queries),'numeric_values':len(vals),'wirelength_um':wirelength,
            'buffer_count':sum(n['id'].startswith('B') for n in nodes),
            'buffer_area':sum(lib[n['cell']]['area'] for n in nodes if n['id'].startswith('B'))}
    if p.returncode or tool_errors or p.stderr or len(vals)!=len(queries) or not all(map(math.isfinite,vals)):
        result['status']='TOOL_OR_OBSERVATION_ERROR'
    else:
        observations=[dict(kind=k,pin=pin,transition=tr,value=v) for (k,pin,tr),v in zip(queries,vals)]
        (out/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
        arrivals=[o['value'] for o in observations if o['kind']=='arrival']
        result.update(timing_metrics(arrivals,f))
        result['max_output_Y_slew_ps']=max(o['value'] for o in observations if o['kind']=='slew')
        result['max_input_A_slew_ps']=max(o['value'] for o in observations if o['kind']=='input_slew')
        slewerrors=[]
        if result['max_output_Y_slew_ps']>f['max_slew_ps']:slewerrors.append('Y_output_slew')
        if result['max_input_A_slew_ps']>f['max_slew_ps']:slewerrors.append('A_input_slew')
        result['geometric_or_electrical_errors']+=slewerrors
        result['required_times_ps']=sorted(set(o['value'] for o in observations if o['kind']=='required'))
        result['required_time_matches_config']=all(abs(v-f['required_ps'])<1e-6 for v in result['required_times_ps'])
        bykey={(o['kind'],o['pin'],o['transition']):o['value'] for o in observations}
        slack_residual=max(abs(bykey['slack',f'y{i}',tr]-(f['required_ps']-bykey['arrival',f'y{i}',tr])) for i in range(len(f['sinks'])) for tr in ['rise','fall'])
        result['slack_consistency_max_residual_ps']=slack_residual
        if not result['required_time_matches_config'] or slack_residual>0.002:
            result['status']='CONSTRAINT_OR_METRIC_ERROR'
        elif result['geometric_or_electrical_errors']:result['status']='DECLARED_CONSTRAINT_VIOLATION'
        else:result['status']='TIMING_VIOLATION' if result['tns_ps']<0 else 'TIMING_FEASIBLE_UNDER_DECLARED_MODEL'
        path=[]
        for line in p.stdout.splitlines():
            m=re.match(r'\s*pin\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+(rise|fall)\s+(\S+)',line)
            if m:path.append({'delay_ps':float(m[1]),'arrival_ps':float(m[2]),'transition':m[4],'pin':m[5]})
        result['critical_path_cell_delay_ps']=sum(x['delay_ps'] for x in path if x['pin'].endswith(':Y'))
        result['critical_path_wire_delay_ps']=sum(x['delay_ps'] for x in path if x['pin'].endswith(':A'))
        result['critical_path_driver_delay_ps']=sum(x['delay_ps'] for x in path if x['pin']=='D:Y')
        result['critical_path_rows']=path
        result['critical_path_sum_residual_ps']=abs(sum(x['delay_ps'] for x in path)-result['max_arrival_ps'])
        if result['critical_path_sum_residual_ps']>0.01:result['status']='PATH_ACCOUNTING_ERROR'
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--engine',required=True);a=ap.parse_args()
    target=ROOT/'metrics'/'feasibility.json'
    if target.exists():raise SystemExit('Existing diagnostic evidence: refusing to rerun or overwrite.')
    planpath=ROOT/'config'/'feasibility_plan.json';plan=json.loads(planpath.read_text())
    assert plan['maximum_configurations']==9 and len(plan['cases'])==3
    _,lib=library();libpath=ROOT/'vendor'/'asap7.lib'
    rows=[];start=time.perf_counter()
    for name in plan['cases']:
        f=fixture(name)
        baseline=json.loads((ROOT/'runs'/name/'geometric-3'/'decoded_tree.json').read_text())
        candidates=[('archived_geometric_3',baseline),('shallow_x8_10pct',shallow(f,.1)),('shallow_x8_50pct',shallow(f,.5))]
        for label,tree in candidates:
            assert len(rows)<9
            r=run_case(f,label,tree,a.engine,libpath,lib);rows.append(r);print(json.dumps(r),flush=True)
    result={'plan_sha256':hashlib.sha256(planpath.read_bytes()).hexdigest(),'configuration_count':len(rows),
        'actual_sta_calls':len(rows),'sta_wall_seconds':sum(r['sta_wall_seconds'] for r in rows),
        'total_wall_seconds':time.perf_counter()-start,'model_or_api_calls':0,'training_steps':0,'physical_runs':0,
        'scope':'Declared fixture checks plus new A/Y observations; no full electrical/physical legality or infeasibility proof.',
        'rows':rows}
    target.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
