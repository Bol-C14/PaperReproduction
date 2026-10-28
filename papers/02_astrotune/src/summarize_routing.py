"""Offline v3 protocol audit. No EDA, network, or model invocation."""
import json,re,hashlib,csv,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'routing_v3';rows=[json.loads(l) for l in (B/'attempts.jsonl').read_text().splitlines()];by={r['attempt']:r for r in rows};assert len(rows)==15
def local_db(path,digest):
 if '/routing_v3/' in path:return B/path.split('/routing_v3/',1)[1]
 return B/'inputs'/(digest+'.odb')
for r in rows:
 assert hashlib.sha256(local_db(r['input_db'],r['input_db_sha256']).read_bytes()).hexdigest()==r['input_db_sha256']
 if r['status']=='ok':assert hashlib.sha256(local_db(r['output_db'],r['output_db_sha256']).read_bytes()).hexdigest()==r['output_db_sha256']
for i in (4,8,9,10,11):
 log=(ROOT/by[i]['out']/'tool.log').read_text();assert re.findall(r'Number of violations = (\d+)',log)[-1]=='0';assert not (ROOT/by[i]['out']/'drc.rpt').read_text().strip()
for i,j in ((12,9),(13,10),(14,11)):
 assert by[i]['input_db_sha256']==by[j]['output_db_sha256']
 assert 'read_spef ' in (ROOT/by[i]['out']/'run.tcl').read_text()
 assert '*RES' in (ROOT/by[j]['out']/'routed.spef').read_text()
early={0:by[6],9:by[7]['early_metrics']};final={0:by[13],9:by[14]}
def dominate(a,b):return a['area']<=b['area'] and a['power']<=b['power'] and a['slack']>=b['slack'] and (a['power']<b['power'] or a['slack']>b['slack'] or a['area']<b['area'])
assert dominate(early[9],early[0]) and dominate(final[9],final[0]);assert by[12]['power']==by[14]['power'] and by[12]['slack']==by[14]['slack']
pairs=[]
for p in (0,9):pairs.append({'design':'adder_32bit','s':0,'p':p,'early_area_um2':early[p]['area'],'early_power_w':early[p]['power'],'early_slack_ns':early[p]['slack'],'final_area_um2':final[p]['area'],'final_power_w':final[p]['power'],'final_slack_ns':final[p]['slack'],'final_db_sha256':final[p]['input_db_sha256']})
with (B/'metrics.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(pairs[0]),lineterminator='\n');w.writeheader();w.writerows(pairs)
# Charge original artifact-producing history by actual run/id, not merely content hash.
history={}
for i in (3,7):
 parent=by[i]['parent_placement'];history[parent['run'],parent['id']]=parent
 source=[json.loads(l) for l in (ROOT/'results'/(parent['parent_run']+'.jsonl')).read_text().splitlines()];syn=next(x for x in source if x['id']==parent['parent_id']);history[syn['run'],syn['id']]=syn
preparation_wall=sum(x['wall_s'] for x in history.values())+by[3]['wall_s']+by[7]['wall_s'];policies=[]
for name,ids in [('single_parent_p9_two_seeds',[9,11,12,14]),('top2_each_seed0',[10,11,13,14])]:
 a=[by[i] for i in ids];fin=[by[i] for i in ids if by[i]['stage']=='spef_audit'];best=min(fin,key=lambda r:r['power']);policies.append({'policy':name,'new_stage_calls_charged':4,'route_extract_calls':2,'spef_audit_calls':2,'same_tool_time_allowance_s':24,'actual_new_tool_wall_s':sum(x['wall_s'] for x in a),'shared_preparation_calls_charged':len(history)+2,'shared_preparation_wall_s_charged':preparation_wall,'all_in_calls_per_policy':4+len(history)+2,'best_final_area':best['area'],'best_final_power':best['power'],'best_final_slack':best['slack'],'best_row_attempt':best['attempt'],'unique_parent_placements':len({x['p'] for x in fin}),'unique_routed_db_hashes':len({x['input_db_sha256'] for x in fin})})
regret=max(0,policies[0]['best_final_power']-policies[1]['best_final_power'])
result={'actual_openroad_evaluation_calls':15,'tool_successes':sum(r['status']=='ok' for r in rows),'tool_failures':sum(r['status']!='ok' for r in rows),'total_tool_wall_s':sum(r['wall_s'] for r in rows),'frozen_original_cap':12,'explicit_correctness_repair_calls':3,'final_cap':15,'actual_new_rtl_synthesis_calls':0,'standalone_new_placement_calls':0,'nested_global_placement_operations':2,'actual_completed_global_routes':3,'actual_completed_detailed_routes':5,'read_spef_final_validation_calls':3,'control_help_version_invocations_not_eda':3,'strict_placement_to_final_rank_reversals':0,'observed_early_pruning_power_regret_w':regret,'pareto_frontier_early_p':[9],'pareto_frontier_final_p':[9],'final_metrics_use_attempts':[12,13,14],'extraction_produced_but_not_explicitly_consumed_attempts':[5,8,9,10,11],'do_not_use_as_final_extracted_timing':[4,5,8,9,10,11],'paired_policies':policies,'original_attempts_retained':3092,'cumulative_eda_attempts_including_v3':3107,'cumulative_successes':3101,'cumulative_failures':6,'llm_api_calls':0,'stop_reason':'No corrected rank reversal or Pareto tradeoff; no top2 best-PPA gain. Stop after fixed paired check, no divider or further sweep.','limits':'One small combinational RTL, fixed synthesis; ideal supply/no power-grid/signoff/LVS, not seven stages. Paired common evaluation reused once physically but charged in each policy. Equal call counts/time allowances, not identical realized tool time. No cold-start speedup claim.'}
(B/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
