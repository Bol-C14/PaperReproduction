"""Independent artifact checks from raw verdicts, not the replay's scoring functions."""
import sys,pathlib,json,hashlib,itertools
import numpy as np,pandas as pd
root=pathlib.Path(sys.argv[1]); assets=root/'assets/arena-hard'; out=root/'results/arena-hard'
load=lambda p:json.loads(p.read_text())
plan=load(assets/'selection-plan.json'); base=plan['baseline']; models=plan['models']; checks=[]
assert hashlib.sha256((assets/'selection-plan.json').read_bytes()).hexdigest()=='ff9b26c4c0aeb277d28a1817978a72f5555eccb81cfa34d7ba44bb4727a37528'
for r in load(assets/'acquisition.json'):
 assert r['status']=='downloaded'; p=assets/r['path']; assert p.stat().st_size==r['bytes']; assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
checks.append('all61_downloaded_file_hashes_and_frozen_selection')
qids=load(out/'selected_questions.json')['all']; common=load(out/'matched_questions.json')['ids']; stats=load(out/'primary.json')['stats']
verdicts={'A=B':(0.5,1),'A>B':(0.,1),'A>>B':(0.,3),'B>A':(1.,1),'B>>A':(1.,3)}
raw={}; totals={}; identity=[]
for j in plan['judges']:
 raw[j]={}
 for m in models:
  if m==base:continue
  rs=[json.loads(l) for l in (assets/f'data/arena-hard-v0.1/model_judgment/{j}/{m}.jsonl').read_text().splitlines()]
  assert all(r['baseline']==base and r['model']==m for r in rs)
  recorded=sorted(set(r['judge'] for r in rs));identity.append({'directory':j,'model':m,'recorded_judges':recorded,'directory_matches_recorded':recorded==[j]})
  raw[j][m]={r['uid']:r for r in rs}
  if j==plan['judges'][0]:
   win=0.;den=0
   for r in rs:
    for game,g in enumerate(r['games']):
     if g['score'] not in verdicts:continue
     credit,w=verdicts[g['score']];credit=credit if game==0 else 1-credit;win+=w*credit;den+=w
   assert abs(stats[m]['score']-100*win/den)<1e-10
checks.append('raw_baseline_model_identity_and_independent_primary_scores; judge_label_mismatch_explicitly_reported')
(out/'judge_identity.json').write_text(json.dumps(identity,indent=2)+'\n')
def answer_content(msg):
 c=msg.get('content')
 return c.get('answer') if isinstance(c,dict) else c
answer_checks=[]; answer_texts={}
for m in models:
 rs=[json.loads(l) for l in (assets/f'data/arena-hard-v0.1/model_answer/{m}.jsonl').read_text().splitlines()]
 invalid=[];markers=[];answer_texts[m]={r['uid']:[answer_content(msg) for msg in r.get('messages',[]) if msg.get('role')=='assistant'] for r in rs}
 for r in rs:
  texts=[answer_content(msg) for msg in r.get('messages',[]) if msg.get('role')=='assistant']
  if not texts or any(not isinstance(t,str) or not t.strip() for t in texts):invalid.append(r['uid'])
  if any(isinstance(t,str) and t.strip()=='$ERROR$' for t in texts):markers.append(r['uid'])
 answer_checks.append({'model':m,'records':len(rs),'empty_or_missing_assistant_ids':invalid,'literal_upstream_error_marker_ids':markers})
(out/'answer_content_checks.json').write_text(json.dumps(answer_checks,indent=2)+'\n')
checks.append('all_released_answers_checked_for_missing_content_and_exact_error_marker')
question_text={r['uid']:r['prompt'] for r in [json.loads(l) for l in (assets/'data/arena-hard-v0.1/question.jsonl').read_text().splitlines()]}
linkage=[]
for j in plan['judges']:
 for m in raw[j]:
  failures=[];n=0
  for q,r in raw[j][m].items():
   for gi,g in enumerate(r['games']):
    n+=1;text=g.get('user_prompt','')
    if not isinstance(text,str) or question_text[q] not in text or any(not isinstance(t,str) or t not in text for t in answer_texts[m][q]+answer_texts[base][q]):failures.append({'question_id':q,'game':gi})
  linkage.append({'judge_directory':j,'model':m,'games':n,'exact_prompt_answer_substring_mismatches':failures})
(out/'response_judgment_linkage.json').write_text(json.dumps(linkage,indent=2)+'\n')
checks.append('all_judgment_input_strings_checked_against_frozen_questions_candidate_and_baseline_answers')

pb=pd.read_csv(out/'primary_question_cluster_bootstrap.csv');ps=load(out/'primary_question_cluster_stats.json')
pidx=np.random.default_rng(20261028).integers(0,len(qids),size=(1000,len(qids)))
for m in models:
 assert abs(ps[m]['lower']-np.percentile(pb[m],2.5))<1e-10;assert abs(ps[m]['upper']-np.percentile(pb[m],97.5))<1e-10
 if m==base:continue
 credits=[];weights=[]
 for q in qids:
  wc=0.;wt=0
  for gi,g in enumerate(raw[plan['judges'][0]][m][q]['games']):
   if g['score'] not in verdicts:continue
   credit,w=verdicts[g['score']];wc+=w*(credit if gi==0 else 1-credit);wt+=w
  credits.append(wc);weights.append(wt)
 credits=np.array(credits);weights=np.array(weights)
 for k in [0,1,999]:assert abs(100*credits[pidx[k]].sum()/weights[pidx[k]].sum()-pb.iloc[k][m])<1e-10
checks.append('full500_primary_cluster_draws_and_intervals_independently_recomputed')
indices=np.random.default_rng(20261028).integers(0,len(common),size=(1000,len(common)))
max_boot_error=0.
for j in plan['judges']:
 for mode,games in [('both',[0,1]),('first',[0]),('second',[1])]:
  key=j+'_'+mode;b=pd.read_csv(out/(key+'_bootstrap.csv'));s=load(out/(key+'_stats.json'))
  assert b.shape==(1000,20) and np.isfinite(b.values).all();assert (b[base]==50).all()
  for m in models:
   assert abs(s[m]['lower']-np.percentile(b[m],2.5))<1e-10;assert abs(s[m]['upper']-np.percentile(b[m],97.5))<1e-10
   if m==base:continue
   credits=[];weights=[]
   for q in common:
    wc=0.;wt=0
    for gi in games:
     credit,w=verdicts[raw[j][m][q]['games'][gi]['score']];wc+=w*(credit if gi==0 else 1-credit);wt+=w
    credits.append(wc);weights.append(wt)
   credits=np.array(credits);weights=np.array(weights)
   for k in [0,1,999]:
    expected=100*credits[indices[k]].sum()/weights[indices[k]].sum();err=abs(expected-b.iloc[k][m]);max_boot_error=max(max_boot_error,err);assert err<1e-10
  sep=sum(s[x]['lower']>s[y]['upper'] or s[y]['lower']>s[x]['upper'] for x,y in itertools.combinations(models,2))
  assert sep==load(out/'summary.json')[key]['separation']['separated']
checks.append('six_paired_bootstrap_outputs_first_second_last_draws_recomputed_from_raw')
checks.append('all_matched_95percent_intervals_and_pair_separability_recomputed')
orig=load(out/'primary_upstream_upstream_original_stats.json'); corr=load(out/'primary_upstream_stats.json')
sep=lambda s:sum(s[x]['lower']>s[y]['upper'] or s[y]['lower']>s[x]['upper'] for x,y in itertools.combinations(models,2))
quality=load(out/'data_quality.json'); counts={j:{'invalid_records':sum(len(r['invalid']) for r in quality if r['judge']==j),'missing_records':sum(len(r['missing']) for r in quality if r['judge']==j),'duplicates':sum(len(r['duplicates']) for r in quality if r['judge']==j)} for j in plan['judges']}
order=load(out/'order_sensitivity.json'); order_totals={j:{'question_model_pairs':sum(r['questions'] for r in order if r['judge']==j),'direction_disagreements':sum(r['direction_disagreement'] for r in order if r['judge']==j),'five_level_disagreements':sum(r['five_level_disagreement'] for r in order if r['judge']==j),'max_abs_first_minus_second_score':max(abs(r['first_minus_second_score']) for r in order if r['judge']==j)} for j in plan['judges']}
result={'checks':checks,'max_recomputed_bootstrap_error_percentage_points':max_boot_error,'primary_original_separated_pairs':sep(orig),'primary_corrected_separated_pairs':sep(corr),'numerical_correction_changes_separated_pair_count':sep(orig)!=sep(corr),'quality_counts':counts,'judge_identity_mismatch_files':sum(not r['directory_matches_recorded'] for r in identity),'secondary_endpoint_revision_verified':False,'response_judgment_linkage_mismatch_games':sum(len(r['exact_prompt_answer_substring_mismatches']) for r in linkage),'order_totals':order_totals,'human_alignment':'unknown; summary-only comparisons are not paired raw human data'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
