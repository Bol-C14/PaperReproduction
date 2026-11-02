"""Summarize completed physical-only logs; no tool invocation or data repair."""
from pathlib import Path
import hashlib,json,re,statistics
P=Path(__file__).resolve().parents[1];R=P/'logs/physical-only-v2'
rows=json.loads((R/'ledger.json').read_text())
a=[r for r in rows if r['action']=='noop'];b=[r for r in rows if r['action']=='routing_opt']
assert all(r['input_sha256']==rows[0]['input_sha256'] for r in rows)
from identity_v2 import canonical_file as canonical
# Cross-arm/repeat checks beyond the per-process before/after gate.
base=a[0]['arm'];cross=[]
for r in rows:
 d=R/r['arm'];s=(d/'stdout.log').read_text()
 checks={'arm':r['arm'],'same_before_funcsim':canonical(d/'before_funcsim.v')==canonical(R/base/'before_funcsim.v'),'same_before_xdc':canonical(d/'before_constraints.xdc')==canonical(R/base/'before_constraints.xdc'),'route_command_exact':re.findall(r'^Command: route_design.*$',s,re.M)==['Command: route_design -no_psir'],'physopt_commands':re.findall(r'^Command: phys_opt_design.*$',s,re.M),'logged_route_max_cpus':re.findall(r'Multithreading enabled for route_design using a maximum of (\d+) CPUs',s),'output_dcp_sha256':hashlib.sha256((d/'output.dcp').read_bytes()).hexdigest() if (d/'output.dcp').exists() else None}
 cross.append(checks)
assert all(x['same_before_funcsim'] and x['same_before_xdc'] and x['route_command_exact'] and x['logged_route_max_cpus']==['2'] for x in cross)
assert all(x['physopt_commands']==([] if r['action']=='noop' else ['Command: phys_opt_design -routing_opt']) for x,r in zip(cross,rows))
pairs=[{'replicate':i+1,'wns_delta_ns':y['after_clock']['wns_ns']-x['after_clock']['wns_ns'],'cost_ratio_B_over_A':y['wall_seconds']/x['wall_seconds']} for i,(x,y) in enumerate(zip(a,b))]
result={'scope':'one_original_state_physical_only_pipeline_contrast','input_sha256':rows[0]['input_sha256'],'completed_processes':len(rows),'all_recorded_contracts_pass':all(r['contract_pass'] for r in rows),'paired_contrasts':pairs,'median_wns_delta_ns':statistics.median(p['wns_delta_ns'] for p in pairs),'within_arm_wns_range_ns':{k:(max(r['after_clock']['wns_ns'] for r in v)-min(r['after_clock']['wns_ns'] for r in v)) if len(v)>=2 else None for k,v in [('A',a),('B',b)]},'technical_repetitions_per_condition':{'A':len(a),'B':len(b)},'noise_range_established':len(a)>=3 and len(b)>=3,'tool_process_wall_seconds':sum(r['wall_seconds'] for r in rows),'cross_checks':cross,'seed_control':'none_verified; fresh_process_technical_repeats_only','engineering_screen_ns':0.050,'screen_is_significance':False,'states':1,'families':1,'model_requests':0,'paid_resources':False}
(P/'ROUND3_V2_SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
