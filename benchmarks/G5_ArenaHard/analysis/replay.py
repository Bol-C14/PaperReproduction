"""Cached-judgment replay via pinned upstream harness, no generation imports/calls."""
import argparse, pathlib, json, sys, itertools, hashlib, platform, time
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau, norm
p=argparse.ArgumentParser(); p.add_argument('--assets',required=True); p.add_argument('--upstream',required=True); p.add_argument('--out',required=True); a=p.parse_args()
assets=pathlib.Path(a.assets); up=pathlib.Path(a.upstream); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(up)); from show_result import get_battles_from_row
from utils_math import compute_mle_elo,get_bootstrap_result
plan=json.loads((assets/'selection-plan.json').read_text()); models=plan['models']; base=plan['baseline']; judges=plan['judges']; nonbase=[m for m in models if m!=base]
def read(path):
 rows=[json.loads(l) for l in path.read_text().splitlines() if l.strip()]
 for r in rows:
  if 'uid' in r:
   assert 'question_id' not in r; r['question_id']=r['uid']
 return rows
def save(name,obj): (out/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def records(frame): return json.loads(frame.to_json(orient='records'))
def interval_stats(point,boot):
 return {m:{'score':float(point[m]),'lower':float(np.percentile(boot[m],2.5)),'upper':float(np.percentile(boot[m],97.5))} for m in point.index}
def direction(x,y): return 1 if x['lower']>y['upper'] else -1 if y['lower']>x['upper'] else 0
def separation(s):
 pairs=list(itertools.combinations(sorted(s),2)); n=sum(direction(s[x],s[y])!=0 for x,y in pairs)
 return {'separated':n,'pairs':len(pairs),'fraction':n/len(pairs)}
def agreement(s,t):
 pairs=list(itertools.combinations(sorted(set(s)&set(t)),2)); signed=0; cond=0; denom=0; strict=0
 for x,y in pairs:
  d,e=direction(s[x],s[y]),direction(t[x],t[y]); signed+=d*e
  strict+=np.sign(s[x]['score']-s[y]['score'])==np.sign(t[x]['score']-t[y]['score'])
  if e: denom+=1; cond+=(1 if d==e else .5 if d==0 else 0)
 return {'models':sorted(set(s)&set(t)),'pairs':len(pairs),'paper_signed_all_pairs':signed/len(pairs),'notebook_conditional_half_credit':cond/denom if denom else None,'reference_separated_pairs':denom,'point_order_agreement':strict/len(pairs),'spearman':float(spearmanr([s[m]['score'] for m in sorted(set(s)&set(t))],[t[m]['score'] for m in sorted(set(s)&set(t))]).statistic)}
# Deterministic evaluator controls, independent expected outcomes.
controls=[]
for gi in [0,1]:
 for verdict in ['A=B','A>B','A>>B','B>A','B>>A',None]:
  row={'question_id':'control','model':'candidate','games':[{'score':None},{'score':None}]}; row['games'][gi]['score']=verdict
  got=get_battles_from_row(row,False,3,base)
  expected_n=0 if verdict is None else 3 if '>>' in verdict else 1
  expected_w='tie' if verdict=='A=B' else ('model_a' if ((verdict or '').startswith('A')==(gi==0)) else 'model_b')
  ok=len(got)==expected_n and all(r['winner']==expected_w for r in got)
  controls.append({'game':gi,'score':verdict,'expected_n':expected_n,'actual_n':len(got),'ok':ok})
assert all(x['ok'] for x in controls); save('controls.json',controls)
questions=read(assets/'data/arena-hard-v0.1/question.jsonl'); qids=sorted([r['question_id'] for r in questions],key=str); assert len(qids)==len(set(qids))==500
oldq={r['question_id']:r for r in read(up/'data/arena-hard-v0.1/question.jsonl')}
assert set(oldq)==set(qids)
assert all(oldq[r['question_id']]['turns'][0]['content']==r['prompt'] for r in questions)
save('schema_port.json',{'rename':'uid -> question_id','question_ids_equal':True,'all_500_prompts_exact_match_historical':True,'answers_model_field':'model replaces model_id; answers not regenerated'})
save('selected_questions.json',{'all':qids,'pilot':qids[:50]})
raw={}; ledger=[]; validsets=[]
valid={'A=B','A>B','A>>B','B>A','B>>A'}
for j in judges:
 raw[j]={}
 for m in nonbase:
  path=assets/f'data/arena-hard-v0.1/model_judgment/{j}/{m}.jsonl'
  if not path.exists():
   ledger.append({'judge':j,'model':m,'status':'missing_file','missing':qids}); raw[j][m]={}; validsets.append(set()); continue
  rows=read(path); ids=[r['question_id'] for r in rows]; duplicates=sorted({x for x in ids if ids.count(x)>1},key=str)
  good={}; invalid=[]
  for r in rows:
   if r['model']!=m: raise ValueError(('model identity',j,m,r['model']))
   games=r.get('games',[])
   if len(games)!=2 or any(g.get('score') not in valid for g in games): invalid.append({'question_id':r['question_id'],'scores':[g.get('score') for g in games]})
   elif r['question_id'] in qids and r['question_id'] not in duplicates: good[r['question_id']]=r
  raw[j][m]={r['question_id']:r for r in rows if r['question_id'] in qids and r['question_id'] not in duplicates}
  validsets.append(set(good)); ledger.append({'judge':j,'model':m,'status':'offline_replay','rows':len(rows),'duplicates':duplicates,'missing':sorted(set(qids)-set(ids),key=str),'extra_ids':sorted(set(ids)-set(qids),key=str),'invalid':invalid,'valid_complete':len(good)})
save('data_quality.json',ledger)
answers=[]
for m in models:
 rows=read(assets/f'data/arena-hard-v0.1/model_answer/{m}.jsonl'); ids=[r['question_id'] for r in rows]
 answers.append({'model':m,'rows':len(rows),'unique_ids':len(set(ids)),'missing':sorted(set(qids)-set(ids),key=str),'model_ids':sorted(set(r.get('model_id',r.get('model','')) for r in rows))})
save('answer_quality.json',answers)
common=sorted(set.intersection(*validsets),key=str); save('matched_questions.json',{'ids':common,'excluded':sorted(set(qids)-set(common),key=str)})
def battles(j,ms,ids,game=None):
 rows=[]
 for m in ms:
  for q in ids:
   if q not in raw[j][m]: continue
   r=raw[j][m][q]
   if game is None: rows.extend(get_battles_from_row(r,False,3,base))
   else:
    # Keep upstream orientation: ask upstream separately with other game invalid.
    r=dict(r); r['games']=[dict(g) for g in r['games']]; r['games'][1-game]['score']=None
    rows.extend(get_battles_from_row(r,False,3,base))
 return pd.DataFrame(rows)
def rates(df):
 # Closed-form star-graph BT maximum likelihood; validated against unchanged upstream below.
 d={base:50.0}
 for m,g in df.groupby('model_b'):
  d[m]=100*(sum(g.winner=='model_b')+.5*sum(g.winner=='tie'))/len(g)
 return pd.Series(d)
def upstream_result(df,label):
 elo=compute_mle_elo(df,baseline_model=base); point=100/(1+10**((elo[base]-elo)/400)); np.random.seed(42)
 bootelo=get_bootstrap_result(df,compute_mle_elo,100,base); boot=100/(1+10**((bootelo[base].values[:,None]-bootelo)/400))
 err=float(abs(point-rates(df)).max()); assert err<.0001
 s=interval_stats(point,boot); save(label+'_stats.json',s); boot.to_csv(out/(label+'_bootstrap.csv'),index=False)
 return {'stats':s,'separation':separation(s),'battles':len(df),'closed_form_max_abs_error':err}
pilot=upstream_result(battles(judges[0],plan['pilot_models'],qids[:50]),'pilot'); save('pilot.json',pilot)
primarydf=battles(judges[0],nonbase,qids); primary=upstream_result(primarydf,'primary_upstream'); save('primary.json',primary)
primarydf.to_json(out/'primary_battles.jsonl',orient='records',lines=True)
# Paired question bootstrap: independent unit is a prompt, shared across all models and judges.
rng=np.random.default_rng(20261028); indices=rng.integers(0,len(common),size=(1000,len(common)))
matched={}; summary={}; order=[]
for j in judges:
 for mode,game in [('both',None),('first',0),('second',1)]:
  df=battles(j,nonbase,common,game); point=rates(df); boots={base:np.full(1000,50.)}
  for m in nonbase:
   subset=df[df.model_b==m]; wins=[]; totals=[]
   for q in common:
    g=subset[subset.question_id==q]; wins.append(sum(g.winner=='model_b')+.5*sum(g.winner=='tie')); totals.append(len(g))
   w=np.array(wins); t=np.array(totals); boots[m]=100*w[indices].sum(1)/t[indices].sum(1)
  b=pd.DataFrame(boots); s=interval_stats(point,b); key=j+'_'+mode; matched[key]=s
  save(key+'_stats.json',s); b.to_csv(out/(key+'_bootstrap.csv'),index=False); summary[key]={'separation':separation(s),'questions':len(common),'battles':len(df)}
  if mode=='both':
   check=compute_mle_elo(df,baseline_model=base); check=100/(1+10**((check[base]-check)/400)); assert float(abs(check-point).max())<.0001
 for m in nonbase:
  ds=[]; exact=[]
  for q in common:
   r=raw[j][m][q]; vals=[]
   for gi in [0,1]:
    score=r['games'][gi]['score']; v=0 if score=='A=B' else (1 if score.startswith('B') else -1)*(2 if '>>' in score else 1); vals.append(v if gi==0 else -v)
   ds.append(np.sign(vals[0])!=np.sign(vals[1])); exact.append(vals[0]!=vals[1])
  order.append({'judge':j,'model':m,'questions':len(common),'direction_disagreement':int(sum(ds)),'five_level_disagreement':int(sum(exact)),'first_minus_second_score':matched[j+'_first'][m]['score']-matched[j+'_second'][m]['score']})
save('order_sensitivity.json',order)
summary['judge_agreement']=agreement(matched[judges[0]+'_both'],matched[judges[1]+'_both'])
for j in judges: summary[j+'_order_agreement']=agreement(matched[j+'_first'],matched[j+'_second'])
# Summary-only human-distribution replay; identity aliases only, no endpoint substitution.
nb=up/'notebook'; mapping=json.loads((nb/'arena_to_arena_hard.json').read_text()); inverse={v:k for k,v in mapping.items()}
cached={inverse[r['model'].lower()]:r for r in read(nb/'bootstrap_stats_arena_hard.jsonl') if r['model'].lower() in inverse}
human={r['model']:r for r in read(nb/'bootstrap_stats_arena_hard_distribution_elo.jsonl')}
summary['official_notebook_20_model_summary']={'models':sorted(cached),'separation':separation(cached),'human_hard_distribution_summary_agreement':agreement(cached,human),'warning':'different model cohort from paper footnote; human cached summary, not raw human-vote reproduction; no pickle loaded'}
save('summary.json',summary)
save('execution.json',{'status':'offline_replay','python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'threads_cap':4,'live_calls':0,'controls_passed':len(controls),'matched_questions':len(common),'human_raw_alignment':'not_run','style_control':'not_run','annotation_pipeline':'not_run'})
print(json.dumps({'primary_separation':primary['separation'],'summary':summary},indent=2),flush=True)
