"""Offline recalculation from recorded metrics. No EDA/model/network required."""
import json,csv,statistics,hashlib,collections,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'
def qp(row,ref):return 100+abs(row['slack']) if row['slack']<0 else .5*row['area']/ref['area']+.5*row['power']/ref['power']
summaries=[json.loads(p.read_text()) for p in sorted(R.glob('*.summary.json'))];rows=[];records=[]
for p in sorted(R.glob('*.jsonl')):
 for l in p.read_text().splitlines():records.append(json.loads(l))
byrun=collections.defaultdict(list)
for r in records:byrun[r['run']].append(r)
legacy=[r for r in records if r['run'].startswith('legacy_')];history_cost=len(legacy);history_wall=sum(s['wall_s'] for s in summaries if s['run'].startswith('legacy_'))
overheads={(r['design'],r['mode']):r['wall_s'] for r in json.loads((R/'retrieval_overhead.json').read_text())}
for s in summaries:
 rr=byrun[s['run']];assert len(rr)==s['calls'];assert all(r['status']=='ok' for r in rr)
 pairs={(r['s'],r['p']) for r in rr if r['stage']=='place'};assert len(pairs)==s['unique_full']
 for r in rr:
  if r['stage']=='place':
   parent=next(x for x in byrun[r['parent_run']] if x['id']==r['parent_id'])
   assert parent['stage']=='synth' and parent['design']==r['design'] and parent['s']==r['s']
   assert r['parent_net_sha256']==parent['net_sha256']==r['net_sha256']
 best=min(qp(r,s['reference']) for r in rr if r['stage']=='place');assert math.isclose(best,s['best_qor'],rel_tol=1e-12)
 m=s['method'];retrieval=m.startswith(('ast','numeric','text','fusion_control'));mode='fusion_control' if m.startswith('fusion_control') else m.split('_')[0]
 extra=overheads.get((s['design'],mode),0) if retrieval else 0
 rows.append({'design':s['design'],'method':m,'seed':s['seed'],'calls':s['calls'],'synth_calls':sum(r['stage']=='synth' for r in rr),'placement_calls':sum(r['stage']=='place' for r in rr),'unique_synth_configs':s['unique_synth'],'unique_full_configs':len(pairs),'unique_netlist_hashes':len({r['net_sha256'] for r in rr if r['stage']=='synth'}),'best_qor':best,'best_area_um2':s['best']['area'],'best_power_w':s['best']['power'],'best_slack_ns':s['best']['slack'],'search_wall_s':s['wall_s'],'eda_wall_s':s['eda_wall_s'],'search_overhead_s':s['wall_s']-s['eda_wall_s'],'retrieval_remeasured_s':extra,'history_calls_charged':history_cost if retrieval else 0,'inclusive_calls':s['calls']+(history_cost if retrieval else 0),'inclusive_wall_estimate_s':s['wall_s']+extra+(history_wall if retrieval else 0),'prunes':sum(e['event']=='prune' for e in s['events']),'promotions':sum(e['event'].endswith('promote') for e in s['events'])})
with (R/'comparison.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
phases=collections.Counter()
for r in records:
 phase='legacy' if r['run'].startswith('legacy_') else 'pilot_debug' if r['run'].startswith('pilot') else 'posthoc_transfer' if r['run'].startswith('transfer_') else 'deterministic_repeat' if r['run'].startswith('repeat_') else 'prune_branch_probe' if 'prune_probe' in r['run'] else 'inclusive_random' if 'inclusive' in r['run'] else 'stress_search' if r['design']=='div_16bit' else 'main_search'
 phases[phase]+=1
ledger={'actual_eda_stage_attempts':len(records),'successful_stage_evaluations':sum(r['status']=='ok' for r in records),'failed_stage_evaluations':sum(r['status']!='ok' for r in records),'phase_stage_attempts':dict(phases),'physical_global_unique_configs':len({(r['design'],r['s'],r['p']) for r in records if r['stage']=='place' and r['status']=='ok'}),'global_unique_synth_configs':len({(r['design'],r['s']) for r in records if r['stage']=='synth' and r['status']=='ok'}),'summed_eda_wall_s':sum(r['wall_s'] for r in records),'main_search_runs':sum(not s['run'].startswith('legacy_') and 'inclusive' not in s['run'] and s['design']!='div_16bit' for s in summaries),'stress_runs':sum(s['design']=='div_16bit' and 'inclusive' not in s['run'] and not s.get('not_performance_arm') for s in summaries),'sum_prunes':sum(row['prunes'] for row in rows),'legacy_db_sha256':hashlib.sha256((R/'legacy_db.json').read_bytes()).hexdigest(),'no_online_llm_calls':True,'llm_calls':0,'accounting_limits':'Original retrieval calls were outside per-search stopwatch. A separate fresh pass is reported explicitly as remeasurement. Inclusive wall is an estimate plus full one-use history cost, not a directly timed end-to-end measurement. Setup/download/model-attempt time is not fully instrumented; no walltime speedup conclusion is supported. Verification/tool setup executions are not EDA search calls.'}
(R/'ledger.json').write_text(json.dumps(ledger,indent=2))
text=['# Recomputed results','', 'All QoR values minimize. 3 seeds are stochastic search runs; deterministic repeats are separate. Main cases and prospectively added div16 stress case are separate strata.','', '| Design | Method | n | Mean QoR | Min–max | Calls/run | Unique full/run | Prunes total |','|---|---|---:|---:|---|---|---|---:|']
groups=collections.defaultdict(list)
for r in rows:
 if r['method']=='random' and r['design'] in ('adder_8bit','multi_pipe_4bit','right_shifter'):continue
 groups[r['design'],r['method']].append(r)
for (d,m),g in sorted(groups.items()):
 vals=[r['best_qor'] for r in g];text.append(f'| {d} | {m} | {len(g)} | {statistics.mean(vals):.8f} | {min(vals):.8f}–{max(vals):.8f} | {min(r["calls"] for r in g)}–{max(r["calls"] for r in g)} | {min(r["unique_full_configs"] for r in g)}–{max(r["unique_full_configs"] for r in g)} | {sum(r["prunes"] for r in g)} |')
text+=['','## Actual execution ledger','', '```json',json.dumps(ledger,indent=2),'```','','`inclusive_calls` charges the ENTIRE 54-call donor database to each retrieval run. `random_inclusive` receives 72 online calls; ordinary runs receive 18 calls. The former is an EDA-count control, not walltime matching.']
(R/'summary.md').write_text('\n'.join(text)+'\n')
# Persist update into a NON-SERVING archive only after tuning; this archive is never a retrieval source in this experiment.
archive={'serving_db_unchanged':True,'history_db_sha256':ledger['legacy_db_sha256'],'entries':[{'design':s['design'],'source_sha256':next(d['sha256'] for d in json.loads((ROOT/'benchmarks/manifest.json').read_text())['designs'] if d['id']==s['design']),'method':s['method'],'seed':s['seed'],'config':[s['best']['s'],s['best']['p']],'metrics':{k:s['best'][k] for k in ('area','power','slack')},'run':s['run']} for s in summaries]}
(R/'archived_db.json').write_text(json.dumps(archive,indent=2))
try:
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 designs=['adder_32bit','multi_pipe_8bit','barrel_shifter','div_16bit'];methods=['random','gp_single','ast_single','numeric_single','text_single','fusion_control_single','ast_tournament','ast_tournament_no_prune','ast_gp_all','ast_tpe_all','random_inclusive']
 fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained')
 for ax,d in zip(axes.flat,designs):
  present=[m for m in methods if groups.get((d,m))]
  for j,m in enumerate(present):
   g=groups.get((d,m),[])
   for i,r in enumerate(g):ax.scatter(j+(i-1)*.12,r['best_qor'],s=26,color='C0' if 'inclusive' not in m else 'C3',alpha=.8)
  ax.set_title(d+(' (separate stress stratum)' if d=='div_16bit' else ''));ax.set_xticks(range(len(present)),present,rotation=65,ha='right',fontsize=8);ax.set_ylabel('Best placed QoR (lower is better)');ax.grid(axis='y',alpha=.2);ax.ticklabel_format(axis='y',style='plain',useOffset=False)
 fig.suptitle('Real Yosys/OpenROAD runs: 18 stage calls; inclusive random=72\nNo online LLM; each dot is one search seed, not a deterministic repeat',fontsize=13)
 fig.savefig(R/'comparison.png',dpi=160);plt.close(fig)
except ImportError:pass
print(json.dumps(ledger,indent=2))
