"""Recompute round accounting, actual rollback causality and raw-netlist metrics."""
import collections,gzip,hashlib,json,os,shutil
from pathlib import Path
from attribution_round import O,L,C,ROOT,OPS,cone_attribution,metrics_and_attribution,tagged,initial_costs,novel,numerical_update,structural_update,sha
R=ROOT
read=lambda p:json.loads(p.read_text())
ledger=[json.loads(l) for l in (L/'eda_invocations.jsonl').read_text().splitlines()];assert len(ledger)==114 and all(v['returncode']==0 for v in ledger)
sessions=[read(p) for p in sorted((O/'sessions').glob('*.json'))];assert len(sessions)==8
runs=[read(p) for p in sorted((O/'runs').glob('*.json'))];assert len(runs)==52 # 48 complete +4 successful FIR partial
for s in sessions:
 s['unique_observed_gate_depth_pairs']=len({(v['gates'],v['depth']) for v in s['observed_paired_metrics']})
 assert s['queries']==6 and s['unique_rtl']==6 and s['duplicate_rate']==0
 assert len({read(O/'runs'/f'{i}.json')['metrics']['rtl_sha256'] for i in s['record_ids']})==6
for name in {s['fixture'] for s in sessions}:assert len({s['graph_sha256'] for s in sessions if s['fixture']==name})==1
# Reconstruct the four pilot metrics plus failed gate, without executing tools.
pilots=read(O/'pilot_successors.json');all_metrics={}
for p in pilots:
 all_metrics[p['base']['id']]=p['base'];all_metrics[p['successor']['id']]=p['successor']
for r in runs:all_metrics[r['id']]=r['metrics']
failures=[read(p) for p in (O/'failures').glob('*.json')]
for f in failures:all_metrics[f['metrics']['id']]=f['metrics']
assert len(all_metrics)==57
rollback=[];increases=decreases=0
for s in sessions:
 rows=[read(O/'runs'/f'{i}.json') for i in s['record_ids']]
 for j,r in enumerate(rows):
  increases+=sum(d['direction']=='increase' for d in r['action']['deltas'].values());decreases+=sum(d['direction']=='decrease' for d in r['action']['deltas'].values())
  if r['action']['rollback']:
   a=r['action'];executed=j+1<len(rows)
   if executed:assert rows[j+1]['metrics']['rtl_sha256']==a['actual_successor_rtl_sha']
   rollback.append(dict(id=r['id'],nonterminal=executed,changes_unconstrained_next=a['rollback_changes_raw_extraction'],changes_novel_next=a['rollback_changes_novel_successor'],actual_successor_confirmed=executed and rows[j+1]['metrics']['rtl_sha256']==a['actual_successor_rtl_sha'],counterfactual_scope='same frozen graph, same previously seen set; no extra EDA for unused branch'))
# Standalone original JSON representatives for each emitted-RTL hash.
groups=collections.defaultdict(list)
for ident,m in all_metrics.items():
 src=O/'rtl'/f'{ident}.v';assert hashlib.sha256(src.read_bytes()).hexdigest()==m['rtl_sha256'];assert 'SUCCESS!' in gzip.decompress((L/f'{ident}_rtl_sat.log.gz').read_bytes()).decode();groups[m['rtl_sha256']].append((ident,m))
folder=O/'unique_netlists';folder.mkdir(exist_ok=True);inventory=[]
for h,members in sorted(groups.items()):
 ident,m=members[0];net=R/Path(os.environ.get('ASPEN_ATTRIBUTION_RUN_ROOT','.'))/'results/netlists/attribution_round'/f'{ident}.json';raw=net.read_bytes();assert hashlib.sha256(raw).hexdigest()==m['netlist_sha256'];dest=folder/f'{h}.json';dest.write_bytes(raw)
 # Recompute actual generic gate/depth independent of saved source coverage.
 dummy=metrics_and_attribution(dest,O/'rtl'/f'{ident}.v',{});assert (dummy['gates'],dummy['depth'])==(m['gates'],m['depth'])
 inventory.append(dict(rtl_sha256=h,netlist_sha256=m['netlist_sha256'],representative_id=ident,path=str(dest.relative_to(O)),gates=m['gates'],depth=m['depth'],member_ids=[i for i,v in members]))
coverage=[dict(id=i,cell_coverage=m['coverage'],named_node_coverage=m['named_node_coverage'],gates=m['gates']) for i,m in all_metrics.items()]
summary=dict(complete_sessions=8,complete_comparison_synthesis=48,partial_fir_synthesis=5,pilot_synthesis=4,total_synthesis=57,total_rtl_sat=57,eda_ledger_entries=114,eda_nonzero_exits=0,unique_emitted_rtl=len(groups),per_complete_arm_unique=6,round_hard_cap=64,reserve_reason='FIR named-node coverage gate failed at q4; prospectively recorded replacement; no remaining FIR arms',increase_updates=increases,decrease_updates=decreases,total_rollbacks=len(rollback),nonterminal_rollbacks=sum(r['nonterminal'] for r in rollback),nonterminal_changed_successor=sum(r['nonterminal'] and r['changes_novel_next'] and r['actual_successor_confirmed'] for r in rollback),complete_session_wall_seconds=sum(s['wall_seconds'] for s in sessions),eda_wall_seconds=sum(v['seconds'] for v in ledger),source_route='cell src coverage0 pruned; named-wire cone fractional allocation substitute',proof_scope='SAT checks generated RTL-to-reference, not synthesized netlist equivalence',model_api_calls=0,paid_cost_usd=0)
for name,v in [('validation.json',summary),('rollback_effects.json',rollback),('coverage.json',coverage),('unique_netlist_inventory.json',inventory),('comparison_summary.json',sessions)]: (O/name).write_text(json.dumps(v,indent=2))
print(json.dumps(dict(validation=summary,results=[dict(fixture=s['fixture'],width=s['width'],policy=s['policy'],external_best_gates=s['external_best_gates'],last_candidate=s['last_candidate']) for s in sessions]),indent=2))
