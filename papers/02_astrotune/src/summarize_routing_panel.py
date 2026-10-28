"""Self-contained offline v4 audit; no EDA/model/network calls."""
import json,csv,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'routing_v4';r=list(map(json.loads,(B/'attempts.jsonl').read_text().splitlines()));assert len(r)<=8

def localdb(path,digest):
 if '/routing_v4/' in path:return B/path.split('/routing_v4/',1)[1]
 return B/'inputs'/(digest+'.odb')
for x in r:
 assert hashlib.sha256(localdb(x['input_db'],x['input_db_sha256']).read_bytes()).hexdigest()==x['input_db_sha256']
 if x['status']=='ok':assert hashlib.sha256(localdb(x['output_db'],x['output_db_sha256']).read_bytes()).hexdigest()==x['output_db_sha256']
assert all(x['status']=='ok' for x in r),'incomplete/failed panel needs separate invalid-case reporting'
connect=json.loads((B/'spef_connectivity.json').read_text());assert len(connect)==4 and all(x['disconnected_terminal_graph_nets']==0 for x in connect)
rows=[];comparison=[];history=[]
def dominates(a,b):return a['area']<=b['area'] and a['power']<=b['power'] and a['slack']>=b['slack'] and any((a['area']<b['area'],a['power']<b['power'],a['slack']>b['slack']))
def q(a,ref):return 100+abs(a['slack']) if a['slack']<0 else .5*a['area']/ref['area']+.5*a['power']/ref['power']
for design,s in [('div_16bit',0),('adder_32bit',3)]:
 subset=[x for x in r if x['design']==design];globals={x['p']:x for x in subset if x['stage']=='global'};finals={x['p']:x for x in subset if x['stage']=='detail_extract'};assert set(globals)==set(finals)=={0,9}
 early={p:x['early_metrics'] for p,x in globals.items()};ref=early[0]
 for p,x in finals.items():
  g=globals[p];assert x['input_db_sha256']==g['output_db_sha256'];log=(ROOT/x['out']/'tool.log').read_text();script=(ROOT/x['out']/'run.tcl').read_text();assert 'read_spef ' in script and re.findall(r'Number of violations = (\d+)',log)[-1]=='0' and not (ROOT/x['out']/'drc.rpt').read_text().strip();assert '*RES' in (ROOT/x['out']/'routed.spef').read_text()
  rows.append({'design':design,'s':s,'p':p,'area_um2':x['area'],'early_power_w':early[p]['power'],'early_slack_ns':early[p]['slack'],'final_power_w':x['power'],'final_slack_ns':x['slack'],'early_qor':q(early[p],ref),'final_qor':q(x,ref),'actual_tool_calls':2,'tool_time_allowance_s':180,'actual_tool_wall_s':g['wall_s']+x['wall_s'],'final_db_sha256':x['output_db_sha256'],'final_spef_sha256':hashlib.sha256((ROOT/x['out']/'routed.spef').read_bytes()).hexdigest(),'global_estimate_missing_pin_warnings_before_rcx':log.count('Missing route to pin')})
 ev={p:q(a,ref) for p,a in early.items()};fv={p:q(a,ref) for p,a in finals.items()};eb=min(ev,key=ev.get);fb=min(fv,key=fv.get);strict=(ev[0]-ev[9])*(fv[0]-fv[9])<0
 front=lambda vals:[p for p in vals if not any(dominates(vals[j],vals[p]) for j in vals if j!=p)]
 minima={'area':min(x['area'] for x in finals.values()),'power':min(x['power'] for x in finals.values()),'slack':max(x['slack'] for x in finals.values())};joint=[p for p,a in finals.items() if all(a[k]==v for k,v in minima.items())]
 hist={}
 for g in globals.values():
  p=g['parent_placement'];hist[p['run'],p['id']]=p;rr=list(map(json.loads,(ROOT/'results'/(p['parent_run']+'.jsonl')).read_text().splitlines()));syn=next(a for a in rr if a['id']==p['parent_id']);hist[syn['run'],syn['id']]=syn
 prep=len(hist)+2;prepwall=sum(a['wall_s'] for a in hist.values())+sum(a['wall_s'] for a in globals.values())
 comparison.append({'design':design,'s':s,'early_qor':ev,'final_qor':fv,'strict_qor_rank_reversal':strict,'early_choice':eb,'final_choice':fb,'early_pruning_qor_regret':fv[eb]-min(fv.values()),'early_pareto_p':front(early),'final_pareto_p':front(finals),'independent_final_extrema':minima,'one_implementation_attains_all_extrema':joint,'prepared_history_calls_charged_to_both':prep,'prepared_history_wall_s_charged_to_both':prepwall,'policy_analysis':'Observed panel replay only. B=1 both policies take early-best. At B=2 top2 can inspect both; fixed-parent has only one allowed routing setting. Thus no equal-actual-EDA optimizer superiority claim; do not spend a deterministic duplicate to manufacture matching.','single_parent_cold_final_calls':1,'top2_cold_final_calls':2,'single_parent_best_final_qor':fv[eb],'top2_observed_best_final_qor':min(fv.values()),'replay_true_eda_calls':0})
with (B/'metrics.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
result={'actual_new_tool_calls':len(r),'actual_new_detailed_evaluations':sum(x['stage']=='detail_extract' for x in r),'actual_new_global_route_calls':sum(x['stage']=='global' for x in r),'tool_successes':sum(x['status']=='ok' for x in r),'tool_failures':sum(x['status']!='ok' for x in r),'actual_total_tool_wall_s':sum(x['wall_s'] for x in r),'total_allowance_s':720,'per_candidate_calls':2,'per_candidate_time_allowance_s':180,'eda_response_cache_hits':0,'unique_detailed_configs':len(rows),'unique_routed_hashes':len({x['final_db_sha256'] for x in rows}),'llm_api_calls':0,'new_synthesis_calls':0,'new_standalone_placement_calls':0,'nested_placement_repair_operations':4,'prior_attempts_preserved':3107,'cumulative_attempts':3107+len(r),'cumulative_successes':3101+sum(x['status']=='ok' for x in r),'cumulative_failures':6+sum(x['status']!='ok' for x in r),'comparison':comparison,'strict_rank_reversals':sum(x['strict_qor_rank_reversal'] for x in comparison),'stop':'Frozen panel complete; no additional candidates, stages or models. Mechanism evidence only, not online-policy/LLM/7-stage/generic-family efficacy.'}
(B/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
