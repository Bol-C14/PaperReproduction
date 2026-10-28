"""Summarize sanitized verdict vectors; no task inputs or source answers required."""
import hashlib,json,os,pathlib,random
ROOT=pathlib.Path(__file__).resolve().parents[1];P=pathlib.Path(os.environ.get('EVALPLUS_EVIDENCE',str(ROOT/'results')))
dev=json.loads((P/'development/all-results.json').read_text());held=json.loads((P/'held_out/all-results.json').read_text());frozen=json.loads((P/'frozen-reduction.json').read_text())
allrows={r['task_id']:r for r in dev}; models={m:dev for m in ['chatgpt','codegen-2b']};models['gpt-4']=held
valid=[r['task_id'] for r in dev if r['task_id']!='HumanEval/32']; summary={'status':'offline_replay','selection_count':20,'calibrated_tasks':19,'quarantined':[{'task_id':'HumanEval/32','reason':'upstream special-oracle successful branches omit result/progress bookkeeping; reference replay fails'}],'models':{},'timeouts':[],'all_selected_tasks':list(allrows)}
def passed(row,model):return all(row['variants'][model][s]['status']=='pass' and len(row['variants'][model][s]['details'])==row['variants'][model][s]['expected_count'] and all(row['variants'][model][s]['details']) for s in ['base','plus'])
for m,rows in models.items():
 good=[r for r in rows if r['task_id'] in valid]; out={'unique_cached_programs':20,'evaluator_invalid':1,'base_pass':0,'augmented_pass':0,'base_false_accepts':[],'base_definite_fail':0,'augmented_unknown':0,'reduction_projection':{}}
 for r in good:
  v=r['variants'][m];base=v['base']['status']=='pass';full=passed(r,m);out['base_pass']+=base;out['augmented_pass']+=full;out['base_definite_fail']+=not base
  if base and v['plus']['status']=='fail':out['base_false_accepts'].append(r['task_id'])
  if base and v['plus']['status']=='timeout':out['augmented_unknown']+=1
  for suite in ['base','plus']:
   s=v[suite]
   if s['status']=='timeout':summary['timeouts'].append({'model':m,'task_id':r['task_id'],'suite':suite,'recorded':len(s['details']),'expected':s['expected_count'],'base_failed':not base})
 for kind in ['samples','coverage','mutation','combined']:
  n=0;falseaccept=[];unknown=[]
  for r in good:
   v=r['variants'][m];idx=frozen['tasks'][r['task_id']]['selected_plus_indices'][kind];d=v['plus']['details']
   if v['base']['status']!='pass' or any(i<len(d) and not d[i] for i in idx):continue
   if any(i>=len(d) for i in idx):unknown.append(r['task_id']);continue
   n+=1
   if not passed(r,m):falseaccept.append(r['task_id'])
  out['reduction_projection'][kind]={'pass':n,'missed_vs_full':falseaccept,'unknown':unknown}
 summary['models'][m]=out
summary['tests']={'base':sum(r['variants']['reference']['base']['expected_count'] for r in dev if r['task_id'] in valid),'plus':sum(r['variants']['reference']['plus']['expected_count'] for r in dev if r['task_id'] in valid),'reduced_plus':{k:sum(len(v['selected_plus_indices'][k]) for tid,v in frozen['tasks'].items() if tid in valid) for k in ['samples','coverage','mutation','combined']}}
summary['contracts']={'base':sum(r['contracts']['base']['count'] for r in dev),'plus':sum(r['contracts']['plus']['count'] for r in dev),'violations':[{'task_id':r['task_id'],'suite':s,'count':len(r['contracts'][s]['invalid'])} for r in dev for s in ['base','plus'] if r['contracts'][s]['invalid']]}
mut={'generated':0,'killed':0,'survived_unresolved':0,'no_eligible_comparison':[],'known_equivalent_wrapper_pass':0,'equivalent_wrapper_evaluator_invalid':1}
for r in dev:
 if r['task_id'] not in valid:continue
 if passed(r,'equivalent_wrapper'):mut['known_equivalent_wrapper_pass']+=1
 if 'comparison_mutant' not in r['variants']:mut['no_eligible_comparison'].append(r['task_id']);continue
 mut['generated']+=1
 if passed(r,'comparison_mutant'):mut['survived_unresolved']+=1
 else:mut['killed']+=1
summary['implementation_mutants_calibrated']=mut
rng=random.Random(20261028);B=20000
matrix={m:{r['task_id']:int(passed(r,m)) for r in rows if r['task_id'] in valid} for m,rows in models.items()};ci={}
for a,b in [('gpt-4','chatgpt'),('chatgpt','codegen-2b'),('gpt-4','codegen-2b')]:
 diffs=[matrix[a][t]-matrix[b][t] for t in valid];draws=sorted(sum(rng.choices(diffs,k=19))/19 for _ in range(B))
 ci[a+'_minus_'+b]={'difference':sum(diffs)/19,'percentile_95':[draws[499],draws[19499]],'paired_discordance_a_only':diffs.count(1),'paired_discordance_b_only':diffs.count(-1)}
summary['rank_uncertainty']={'method':'paired task bootstrap; 20000 draws; seed 20261028; descriptive only for purposive calibrated19','comparisons':ci}
combined=P/'combined/all-results.json'
if combined.exists():
 rr=json.loads(combined.read_text());retest={}
 for m in models:
  rows=[r for r in rr if r['task_id'] in valid and r.get('status')=='completed'];n=sum(passed(r,m) for r in rows);retest[m]={'completed_tasks':len(rows),'pass':n,'matches_frozen_projection':n==summary['models'][m]['reduction_projection']['combined']['pass']}
 summary['combined_actual_rerun']=retest
summary['cost_usd']=0
(ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
