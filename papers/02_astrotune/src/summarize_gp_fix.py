"""v2-only metrics and posthoc acquisition replay. Standard library for metrics.
Replay imports sklearn only if available; never executes EDA or changes searches.
"""
import json,csv,statistics,collections,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';rows=[];replay=[]
summaries=[json.loads(p.read_text()) for p in sorted(R.glob('v2pilot_*.summary.json'))]
for su in summaries:
 rr=[json.loads(l) for l in (R/(su['run']+'.jsonl')).read_text().splitlines()];assert len(rr)==su['calls'] and all(x['status']=='ok' for x in rr)
 for child in [r for r in rr if r['stage']=='place']:
  parent=next(r for r in rr if r['id']==child['parent_id']);assert parent['id']<child['id'] and parent['stage']=='synth' and parent['s']==child['s'] and child['parent_run']==su['run']
  assert parent['net_sha256']==child['parent_net_sha256']==child['net_sha256']
 syn=[r for r in rr if r['stage']=='synth'];full=[r for r in rr if r['stage']=='place'];assert len({(r['s'],r['p']) for r in full})==len(full)
 ref=su['reference'];score=lambda x:100+abs(x['slack']) if x['slack']<0 else .5*x['area']/ref['area']+.5*x['power']/ref['power'];assert math.isclose(su['best_qor'],min(map(score,full)))
 inclusive=su['method']=='random_inclusive';assert len(rr)==(62 if inclusive else 8)
 if not inclusive:assert len(syn)<=3
 rows.append({'run':su['run'],'version':'v2_physical_gp','design':su['design'],'method':su['method'],'seed':su['seed'],'true_attempts':len(rr),'synth_calls':len(syn),'unique_synth_configs':len({r['s'] for r in syn}),'unique_full_configs':len(full),'unique_netlist_hashes':len({r['net_sha256'] for r in syn}),'eda_response_cache_hits':0,'best_qor':su['best_qor'],'wall_s':su['wall_s'],'eda_wall_s':su['eda_wall_s'],'history_cost_charged':su.get('history_cost_charged',0),'inclusive_eda_cost':len(rr)+su.get('history_cost_charged',0),'selected_synthesis_ids':[r['s'] for r in syn]})
 try:
  import numpy as np
  from gp_model import gp_pick,acquisition
  from qor import logic
 except ImportError:continue
 if su['method'] not in ('random','random_inclusive'):
  prior={}
  for r in rr:
   if r['stage']=='synth':
    if len(prior)>=2 and r['label']=='search':
     opts=[i for i in range(6) if i not in prior];ids,mu,sd,ei=acquisition(opts,prior,'synth');choice=gp_pick(opts,prior,np.random.default_rng(su['seed']),'synth');assert choice==r['s']
     replay.append({'run':su['run'],'stage':'synth','record_id':r['id'],'observed_metrics_only':True,'actual_choice':r['s'],'replayed_choice':choice,'ei_range':float(np.ptp(ei)),'options':ids,'ei':ei.tolist(),'true_eda_attempts':0,'replay_queries':1})
    prior[r['s']]=logic(r['area'],r['power'],r['slack'],ref)
 if su['method']=='ast_gp_all':
  seen=collections.defaultdict(dict)
  for r in rr:
   if r['stage']!='place':continue
   prior=seen[r['s']]
   if len(prior)>=2:
    opts=[i for i in range(12) if i not in prior];ids,mu,sd,ei=acquisition(opts,prior,'place');choice=gp_pick(opts,prior,np.random.default_rng(su['seed']),'place');assert choice==r['p']
    replay.append({'run':su['run'],'stage':'place','record_id':r['id'],'actual_choice':r['p'],'replayed_choice':choice,'ei_range':float(np.ptp(ei)),'options':ids,'ei':ei.tolist(),'true_eda_attempts':0,'replay_queries':1})
   prior[r['p']]=score(r)
with (R/'gp_fix_comparison.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
if replay:(R/'gp_acquisition_replay.json').write_text(json.dumps(replay,indent=2))
newrecords=[json.loads(l) for p in R.glob('v2pilot_*.jsonl') for l in p.read_text().splitlines()];oldrecords=[json.loads(l) for p in R.glob('*.jsonl') if not p.name.startswith('v2pilot_') for l in p.read_text().splitlines()];newfull={(r['design'],r['s'],r['p']) for r in newrecords if r['stage']=='place'};oldfull={(r['design'],r['s'],r['p']) for r in oldrecords if r['stage']=='place' and r['status']=='ok'}
preparation={s['design']:s.get('retrieval_preparation_wall_s',0) for s in summaries if s.get('retrieval_ranking_reused')}
meta={'actual_fresh_retrieval_preparations':len(preparation),'cached_retrieval_ranking_lookups':sum(bool(s.get('retrieval_ranking_reused')) for s in summaries),'actual_retrieval_preparation_wall_s':sum(preparation.values()),'new_true_attempts_including_pending':len(newrecords),'new_successes':sum(r['status']=='ok' for r in newrecords),'new_failures':sum(r['status']!='ok' for r in newrecords),'unique_full_configs_across_v2':len(newfull),'full_configs_new_to_v1':len(newfull-oldfull),'completed_runs':len(rows),'true_eda_attempts':sum(r['true_attempts'] for r in rows),'eda_response_cache_hits':0,'posthoc_acquisition_replay_queries':len(replay),'posthoc_replay_true_eda_attempts':0,'pilot_synth_cap':3,'synth_space_size':6,'seeds':[0,1],'history_cost_per_retrieval_run':54,'inclusive_random_budget':62,'note':'No v1/v2 pooling. Replay verifies selections using already recorded observations; it is not a new trial, EDA result, or performance arm.'}
(R/'gp_fix_ledger.json').write_text(json.dumps(meta,indent=2))
lines=['# Corrected GP v2 bounded pilot','', 'V1 is retained but cannot evaluate BO efficacy. Each primary run uses8 real calls and at most3/6 synthesis configs; inclusive random uses62 online calls versus retrieval54+8. Two seeds; no significance/generalization claim.','', '| Design | Method | n | Mean best QoR | range | true calls/run | synth configs/run |','|---|---|---:|---:|---|---|---|'];groups=collections.defaultdict(list)
for r in rows:groups[r['design'],r['method']].append(r)
for (d,m),g in sorted(groups.items()):
 vals=[r['best_qor'] for r in g];lines.append(f'| {d} | {m} | {len(g)} | {statistics.mean(vals):.9f} | {min(vals):.9f}–{max(vals):.9f} | {g[0]["true_attempts"]} | {min(r["unique_synth_configs"] for r in g)}–{max(r["unique_synth_configs"] for r in g)} |')
lines+=['','```json',json.dumps(meta,indent=2),'```'];(R/'gp_fix_summary.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
try:
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(1,2,figsize=(13,5),layout='constrained')
 methods=['random','gp_single','ast_single','ast_gp_all','ast_tournament','random_inclusive']
 for ax,d in zip(axes,['multi_pipe_8bit','div_16bit']):
  for j,m in enumerate(methods):
   for i,row in enumerate(groups.get((d,m),[])):ax.scatter(j+(i-.5)*.12,row['best_qor'],color='C3' if m=='random_inclusive' else 'C0')
  ax.set_title(d);ax.set_xticks(range(len(methods)),methods,rotation=40,ha='right');ax.set_ylabel('Best placed QoR (lower is better)');ax.ticklabel_format(axis='y',style='plain',useOffset=False);ax.grid(axis='y',alpha=.2)
 fig.suptitle('Corrected GP v2:8 real stage calls, at most3/6 synth configs\nInclusive random62=history54+online8;2 seeds;no significance claim')
 fig.savefig(R/'gp_fix_comparison.png',dpi=160);plt.close(fig)
except ImportError:pass
