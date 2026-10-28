#!/usr/bin/env python3
"""Offline verification of the nine bounded diagnosis configurations."""
import hashlib,json,re,math
from pilot import ROOT,fixture,library,decode,flatten,validate,timing_metrics
s=json.loads((ROOT/'metrics'/'feasibility.json').read_text());plan=(ROOT/'config'/'feasibility_plan.json').read_bytes()
assert hashlib.sha256(plan).hexdigest()==s['plan_sha256'];assert len(s['rows'])==s['actual_sta_calls']==9
_,lib=library();old={}
for filename in ['pilot.json','aes_pilot.json']:
 for r in json.loads((ROOT/'metrics'/filename).read_text())['rows']:
  if r['method']=='geometric' and r['index']==3:old[r['net']]=r
checked=0
for row in s['rows']:
 f=fixture(row['net']);out=ROOT/'runs'/'feasibility'/row['net']/row['configuration']
 fixed={n['id']:n for n in [f['driver']]+f['sinks']}
 t=decode(json.loads((out/'sequence.json').read_text()),fixed);nodes=flatten(t)
 assert t==json.loads((out/'decoded_tree.json').read_text())
 assert len({n['id'] for n in nodes})==len(nodes)
 assert sum(len(n.get('children',[])) for n in nodes)==len(nodes)-1
 assert not validate(t,f,lib)
 commands=[c for c in (out/'sta.conf').read_text().splitlines() if c.startswith(('report_at ','report_slew ','report_rat ','report_slack '))]
 vals=[float(v) for v in (out/'stdout.txt').read_text().splitlines() if re.fullmatch(r'\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\s*',v)]
 assert len(commands)==len(vals) and all(map(math.isfinite,vals))
 bykey={}
 for c,v in zip(commands,vals):
  parts=c.split();bykey[parts[0],parts[2],parts[-1]]=v
 arrivals=[bykey['report_at',f'y{i}',tr] for i in range(len(f['sinks'])) for tr in ['-rise','-fall']]
 scores=timing_metrics(arrivals,f)
 for k,v in scores.items():assert abs(row[k]-v)<1e-6
 for i in range(len(f['sinks'])):
  for tr in ['-rise','-fall']:
   rat=bykey['report_rat',f'y{i}',tr];slack=bykey['report_slack',f'y{i}',tr]
   assert rat==f['required_ps'] and abs(slack-(rat-bykey['report_at',f'y{i}',tr]))<=.002
 for pin,field in [('A','max_input_A_slew_ps'),('Y','max_output_Y_slew_ps')]:
  assert abs(max(bykey['report_slew',n['id']+':'+pin,tr] for n in nodes for tr in ['-rise','-fall'])-row[field])<1e-6
 assert not re.search(r'^E\s',(out/'engine.log').read_text(),re.M)
 assert not (out/'stderr.txt').read_text()
 assert row['status']=='TIMING_VIOLATION' and not row['geometric_or_electrical_errors']
 if row['configuration']=='archived_geometric_3':
  for k in ['tns_ps','wns_ps','max_arrival_ps']:assert abs(row[k]-old[row['net']][k])<1e-6
 checked+=1
print(json.dumps({'status':'PASS','actual_STA_cases_recomputed':checked,'original_baseline_replays_match':3,'new_A_and_Y_observations_checked':9,'required_and_slack_contract_checked':9,'new_STA_calls_from_verification':0},indent=2))
