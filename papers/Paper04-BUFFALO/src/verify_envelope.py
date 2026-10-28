#!/usr/bin/env python3
"""Offline independent raw-output, load-domain and Pareto recheck of12 calls."""
import hashlib,json,math,re
from pilot import ROOT,blocks,library,flatten,decode,validate,timing_metrics
from audit_units import interpolate


def main():
 s=json.loads((ROOT/'metrics'/'envelope.json').read_text());plan=json.loads((ROOT/'config'/'envelope_plan.json').read_text())
 assert hashlib.sha256((ROOT/'config'/'envelope_plan.json').read_bytes()).hexdigest()==s['plan_sha256']
 assert len(s['rows'])==s['sta_attempt_budget_charged']==12
 text,lib=library();cells=dict(blocks(text,'cell'));old=json.loads((ROOT/'metrics'/'feasibility.json').read_text())
 oldmap={r['net']:r for r in old['rows'] if r['configuration']=='shallow_x8_10pct'}
 checks=0;arcs=[];replays=0
 for r in s['rows']:
  out=ROOT/'runs'/'feasibility'/r['net']/r['configuration'];f=json.loads((out/'fixture.json').read_text());assert f['required_ps']==80 and f['output_load_ff']==r['output_load_ff']
  seq=json.loads((out/'sequence.json').read_text());fixed={n['id']:n for n in [f['driver']]+f['sinks']};tree=decode(seq,fixed);nodes=flatten(tree)
  assert not validate(tree,f,lib)
  assert abs(sum(lib[n['cell']]['area'] for n in nodes if n['id'].startswith('B'))-r['buffer_area'])<1e-8
  commands=[c for c in (out/'sta.conf').read_text().splitlines() if c.startswith(('report_at ','report_slew ','report_rat ','report_slack '))]
  vals=[float(v) for v in (out/'stdout.txt').read_text().splitlines() if re.fullmatch(r'\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\s*',v)]
  assert len(commands)==len(vals) and all(map(math.isfinite,vals))
  bykey={}
  for c,v in zip(commands,vals):
   p=c.split();bykey[p[0],p[2],p[-1]]=v
  arrivals=[bykey['report_at',f'y{i}',tr] for i in range(len(f['sinks'])) for tr in ['-rise','-fall']]
  metrics=timing_metrics(arrivals,f)
  for k,v in metrics.items():assert abs(r[k]-v)<1e-6
  for i in range(len(f['sinks'])):
   for tr in ['-rise','-fall']:
    assert bykey['report_rat',f'y{i}',tr]==80
    assert abs(bykey['report_slack',f'y{i}',tr]-(80-bykey['report_at',f'y{i}',tr]))<.002
  assert not re.search(r'^E\s',(out/'engine.log').read_text(),re.M) and not (out/'stderr.txt').read_text()
  assert r['status']=='TIMING_VIOLATION'
  # Every cell arc independently reconstructed from Liberty and declared geometry.
  for n in nodes:
   for tr in ['rise','fall']:
    cap=f['output_load_ff']
    if n.get('children'):
     cap=0
     for ch in n['children']:
      inp=dict(blocks(cells[ch['cell']],'pin'))['A']
      pc=float(re.search(tr+r'_capacitance\s*:\s*([\d.]+)',inp).group(1))
      cap+=pc+f['c_ff_per_um']*(abs(n['x']-ch['x'])+abs(n['y']-ch['y']))
    pin=dict(blocks(cells[n['cell']],'pin'))['Y'];body=next(blocks(pin,'cell_'+tr))[1]
    slew=bykey['report_slew',n['id']+':A','-'+tr];v,domain=interpolate(body,slew,cap)
    measured=bykey['report_at',n['id']+':Y','-'+tr]-bykey['report_at',n['id']+':A','-'+tr]
    assert abs(v-measured)<.003
    if r['output_load_ff']==1.44:assert domain['load_in_grid'] and domain['input_slew_in_grid']
    arcs.append({'net':r['net'],'configuration':r['configuration'],'node':n['id'],'transition':tr,'load_ff':cap,'residual_ps':abs(v-measured),**domain})
  peers=[q for q in s['rows'] if q['net']==r['net'] and q['output_load_ff']==r['output_load_ff'] and q['pareto_eligible']]
  dominated=any(q['buffer_area']<=r['buffer_area'] and q['max_arrival_ps']<=r['max_arrival_ps'] and (q['buffer_area']<r['buffer_area'] or q['max_arrival_ps']<r['max_arrival_ps']) for q in peers)
  assert r['nondominated_within_panel']==(not dominated)
  assert r['counterfactual_endpoint_feasible']=={str(t):r['max_arrival_ps']<=t for t in plan['counterfactual_required_grid_ps']}
  if r['output_load_ff']==.5:
   assert abs(r['max_arrival_ps']-oldmap[r['net']]['max_arrival_ps'])<1e-6;replays+=1
  checks+=1
 result={'status':'PASS','raw_STA_configurations_recomputed':checks,'old_implementation_replays_match':replays,
         'independent_liberty_cell_arcs':len(arcs),'max_arc_residual_ps':max(a['residual_ps'] for a in arcs),
         'corrected_load_cases':9,'corrected_load_all_arcs_within_characterized_load_and_slew_grid':True,
         'same_boundary_load_pareto_groups_verified':6,'actual_STA_calls_added_by_verification':0,'arcs':arcs}
 (ROOT/'metrics'/'envelope_verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='arcs'},indent=2))

if __name__=='__main__':main()
