import collections,gzip,hashlib,itertools,json,statistics,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/Path(os.environ.get('ASPEN_BEHAVIOR_RUN_ROOT','.'));O=BASE/'results/behavior'
read=lambda p:json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
ss=[read(p) for p in sorted((O/'sessions').glob('factorial*.json'))];assert len(ss)==48
ledger=[json.loads(l) for l in (BASE/'logs/behavior/eda_invocations.jsonl').read_text().splitlines()];assert len(ledger)==692 and all(r['returncode']==0 for r in ledger)
runs=[read(p) for p in (O/'runs').glob('factorial*.json')];assert len(runs)==288
assert all(r['metrics']['rtl_sat'] and r['metrics']['z3']=='unsat' for r in runs)
# Structural contract checks: same starts; genuine positive-cost extraction, no cycles.
starts=collections.defaultdict(set)
for s in ss:starts[s['name']].update(s['initial_graph_hashes']);assert s['true_synthesis_calls']==7 and s['rtl_sat_calls']==7
assert all(len(v)==1 for v in starts.values())
for p in (O/'rtl').glob('*.v'):
 assert p.stat().st_size>0
for p in (BASE/'logs/behavior').glob('*.gz'):gzip.decompress(p.read_bytes())
# No-op extraction recheck verifies adaptation consistency without another synthesis.
from behavior_engine import extract,initial_costs
for graphfile in (O/'graphs').glob('factorial*.json.gz'):
 if graphfile.name.endswith('_build.json.gz'):continue
 g=read(graphfile);extract(g,initial_costs(g),'bottom_up');extract(g,initial_costs(g),'greedy_dag')
effects=[]
for factor in ['pool','selection','cost']:
 others=[v for v in ['pool','selection','cost'] if v!=factor];levels=['initial','expanded'] if factor=='pool' else ['static','feedback']
 for s in ss:
  if s[factor]!=levels[0]:continue
  mate=next(t for t in ss if t['name']==s['name'] and t['seed']==s['seed'] and t[factor]==levels[1] and all(t[k]==s[k] for k in others))
  effects.append(dict(factor=factor,name=s['name'],repeat_label=s['seed'],controls={k:s[k] for k in others},control_gates=s['best_gates'],treatment_gates=mate['best_gates'],gain_percent=100*(s['best_gates']-mate['best_gates'])/s['best_gates'],budget_each=7))
aggregate=[dict(factor=f,paired_comparisons=sum(x['factor']==f for x in effects),mean_gain_percent=statistics.mean(x['gain_percent'] for x in effects if x['factor']==f),warning='descriptive; three controlled fixtures, deterministic repeat labels, no independent random seeds') for f in ['pool','selection','cost']]
summary=[]
for name in sorted({s['name'] for s in ss}):
 for pool in ['initial','expanded']:
  d={}
  for selection,cost in itertools.product(['static','feedback'],repeat=2):d[selection+'_'+cost]=next(s['best_gates'] for s in ss if s['name']==name and s['pool']==pool and s['selection']==selection and s['cost']==cost and s['seed']==0)
  summary.append(dict(name=name,pool=pool,**d))
rep=[]
for s in ss:
 if s['seed']!=0:continue
 t=next(t for t in ss if t['name']==s['name'] and t['pool']==s['pool'] and t['selection']==s['selection'] and t['cost']==s['cost'] and t['seed']==1)
 rep.append(s['best_gates']==t['best_gates'] and s['best_depth']==t['best_depth'])
assert all(rep)
validation=dict(sessions=48,synthesis_calls_factorial=336,sat_calls_factorial=336,pilot_synthesis_calls=7,pilot_sat_calls=7,figure4_synthesis_calls=3,figure4_sat_calls=3,total_new_synthesis=346,total_new_sat=346,eda_ledger_entries=len(ledger),all_eda_exit_success=True,all_336_final_factorial_rtl_sat=True,initial_construction_program_hash_matched=True,deterministic_repeat_agreement=f'{sum(rep)}/{len(rep)}',proposal_finite_unsat=len(read(O/'proposal_validation.json')),feedback_intervention=read(O/'feedback_dependency.json'),wall_seconds_factorial_sum=sum(s['seconds'] for s in ss),graph_seconds=sum(r['graph_seconds'] for r in runs),selected_extractor_seconds=sum(r['extraction']['seconds'] for r in runs),shadow_extractor_seconds=sum(r['greedy_shadow']['seconds'] for r in runs),rule_selection_seconds=sum(r['rule_selection_seconds'] for r in runs),controller_seconds=sum(r['controller_seconds'] for r in runs),model_calls=0,offline_oracle_evaluations=0,cache_hits=0,initialization_note='session wall includes reference eval, graph/rule processing, selected+shadow extraction, controller, all synthesis/SAT, JSON writes; one-time package/install/proposal validation separate')
for p,v in [('factorial_effects.json',effects),('factorial_aggregate.json',aggregate),('factorial_table.json',summary),('validation.json',validation)]: (O/p).write_text(json.dumps(v,indent=2))

pareto=[]
for name in sorted({s['name'] for s in ss}):
 points=[]
 for s in ss:
  if s['name']==name:points.append(dict(id=s['id']+'_reference',gates=s['baseline']['gates'],depth=s['baseline']['depth'],kind='reference'))
 for r in runs:
  if any(s['name']==name and r['id'] in s['records'] for s in ss):points.append(dict(id=r['id'],gates=r['metrics']['gates'],depth=r['metrics']['depth'],kind='extracted'))
 unique={}
 for p in points:unique.setdefault((p['gates'],p['depth']),[]).append(p['id'])
 for (g,d),ids in sorted(unique.items()):
  nondom=not any(a<=g and b<=d and (a<g or b<d) for a,b in unique)
  pareto.append(dict(name=name,gates=g,depth=d,nondominated=nondom,point_ids=ids,scope='factorial sessions only; excludes separate Figure4 intervention'))
(O/'online_pareto.json').write_text(json.dumps(pareto,indent=2))

print(json.dumps(dict(table=summary,effects=aggregate,validation=validation),indent=2))
