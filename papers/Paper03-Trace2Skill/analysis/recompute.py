#!/usr/bin/env python3
"""Independent stdlib audit: never imports upstream validator or expected_results."""
import csv, datetime, hashlib, itertools, json, math, random, statistics
from collections import Counter,defaultdict
from pathlib import Path
P=Path(__file__).resolve().parents[1]; U=next((P/'upstream').iterdir()); E=U/'artifacts/paper-results/evidence'
def rows(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def dump(name,obj): (P/'metrics'/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def wilson(k,n):
 z=1.96;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return [c-h,c+h]
def export(name,data):
 with (P/'metrics'/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator="\n");w.writeheader();w.writerows(data)
report={};taskrows=[];generationrows=[];ablation=[];taskcounts={}
for c in ['C3','C4']:
 r=rows(E/c.lower()/'rollouts.jsonl');q=rows(E/c.lower()/'quality_records.jsonl');tasks=sorted({x['task_id'] for x in r}); taskcounts[c]={}
 coords=[(x['task_id'],x['generation'],x['individual_index'],x['repeat_index']) for x in r]
 assert len(coords)==len(set(coords))==640
 assert set(coords)==set(itertools.product(tasks,range(1,6),range(4),range(4)))
 assert all(x['reward'] in (0,1) and (x['reward']>0)==(x['outcome']=='pass') for x in r)
 assert all(x['outcome'] in ('pass','fail') for x in r)
 for x in r:
  assert x['verify_feedback_attempts']==x['verify_feedback_executions']+x['verify_feedback_budget_rejections']+x['verify_feedback_gate_rejections']
  assert 0<=x['verify_feedback_executions']<=3
 for t in tasks:
  a=[x for x in r if x['task_id']==t];k=sum(x['reward'] for x in a);taskcounts[c][t]=int(k)
  taskrows.append(dict(condition=c,task=t,passes=int(k),attempts=len(a),rate=k/len(a),feedback=sum(x['verify_feedback_executions'] for x in a)))
 qgroups=defaultdict(list)
 for x in q:qgroups[(x['task_id'],x['generation'])].append(x)
 formula_diff=[];qjoin=[]
 for x in q:
  a=[y for y in r if (y['task_id'],y['generation'],y['individual_index'])==(x['task_id'],x['generation'],x['individual_index'])]
  assert len(a)==4 and sum(y['reward'] for y in a)/4==x['pass_at_1']
  s=-1 if x['selection_blocked'] else x['pass_at_1']+.1225*(.55*x['progress_lcb_95']+.15*x['progress_mean']+.2*x['SkillQ']+.1*x['AgentAdherenceQ'])
  assert abs(s-x['SelectQ'])<5.1e-7
  paper=-1 if x['selection_blocked'] else x['pass_at_1']+.1225*(.6*x['progress_lcb_95']+.2*x['progress_mean']+.2*x['SkillQ'])
  formula_diff.append(abs(paper-x['SelectQ']))
 for g in range(1,6):
  a=[x for x in r if x['generation']==g]; b=[x for x in q if x['generation']==g]
  generationrows.append(dict(condition=c,generation=g,passes=int(sum(x['reward'] for x in a)),attempts=len(a),valid=sum(x['valid'] and not x['selection_blocked'] and not x['semantic_floor_violation'] for x in b),all_candidates=len(b)))
 for (t,g),a in qgroups.items():
  live=max(a,key=lambda x:(x['SelectQ'],-x['individual_index']))
  variants={
   'frozen_artifact':lambda x:x['SelectQ'],
   'paper_weights_same_gate':lambda x:-1 if x['selection_blocked'] else x['pass_at_1']+.1225*(.6*x['progress_lcb_95']+.2*x['progress_mean']+.2*x['SkillQ']),
   'sparse_only_same_gate':lambda x:-1 if x['selection_blocked'] else x['pass_at_1'],
   'no_semantic_gate':lambda x:x['pass_at_1']+.1225*(.55*x['progress_lcb_95']+.15*x['progress_mean']+.2*x['SkillQ']+.1),
   'skill_only_same_gate':lambda x:-1 if x['selection_blocked'] else x['SkillQ']}
  for name,fn in variants.items():
   best=max(fn(x) for x in a); winners=[x for x in a if abs(fn(x)-best)<1e-9]; selected=min(winners,key=lambda x:x['individual_index'])
   ablation.append(dict(condition=c,task=t,generation=g,variant=name,selected=selected['individual_index'],archived_formula_winner=live['individual_index'],changed=selected['individual_index']!=live['individual_index'],tie_count=len(winners),archived_winner_in_tie=live in winners,selected_in_sample_pass_rate=selected['pass_at_1']))
 k=int(sum(x['reward'] for x in r))
 report[c]=dict(passes=k,n=len(r),rate=k/len(r),wilson95_naive_iid=wilson(k,len(r)),solved=sum(v>0 for v in taskcounts[c].values()),failure_modes=dict(Counter(x['mode'] for x in r if not x['reward'])),feedback_executions=sum(x['verify_feedback_executions'] for x in r),feedback_attempts=sum(x['verify_feedback_attempts'] for x in r),paper_formula_max_absolute_difference=max(formula_diff),paper_formula_rows_differ_gt_rounding=sum(x>5.1e-7 for x in formula_diff),parent_info_generation1=dict(Counter(x['parent_info'] for x in q if x['generation']==1)))
# Pair only tasks; repeat_index is an on-disk ordinal and does NOT pair random seeds.
deltas=[(taskcounts['C4'][t]-taskcounts['C3'][t])/80 for t in sorted(taskcounts['C3'])];rng=random.Random(260527)
b=sorted(statistics.mean(rng.choices(deltas,k=8)) for _ in range(20000))
report['difference']=dict(rate=statistics.mean(deltas),task_paired_descriptive_bootstrap95=[b[499],b[19499]],task_deltas=deltas,bootstrap_seed=260527,bootstrap_replicates=20000,warning='8 selected tasks, one adaptive search per condition/task; no independent search-seed replication. CI is descriptive, not causal.')
audit=list(csv.DictReader((E/'runtime/llm_calls.csv').open()));retry=list(csv.DictReader((E/'runtime/rollout_retries.csv').open()))
report['runtime_calls']={c:dict(attempts=sum(x['condition']==c for x in audit),purpose=dict(Counter(x['purpose'] for x in audit if x['condition']==c)),status=dict(Counter(x['status'] for x in audit if x['condition']==c)),recorded_optimizer_tokens=sum(int(x['total_tokens'] or 0) for x in audit if x['condition']==c),collection_retry_events=sum(x['condition']==c for x in retry)) for c in ['C3','C4']}
metadata=json.loads((E/'run_metadata.json').read_text()); report['metadata_fields']=sorted(metadata[0])
export('task_results.csv',taskrows);export('generation_results.csv',generationrows);export('selector_replay.csv',ablation)
report['selector_replay_summary']={v:dict(groups=sum(x['variant']==v for x in ablation),changed=sum(x['changed'] for x in ablation if x['variant']==v),ties=sum(x['tie_count']>1 for x in ablation if x['variant']==v),archived_winner_excluded=sum(not x['archived_winner_in_tie'] for x in ablation if x['variant']==v)) for v in sorted({x['variant'] for x in ablation})}
audit96=list(csv.DictReader((E/'agentq96/rollouts.csv').open()))
def auc(field):
 pos=[float(x[field]) for x in audit96 if int(x['passed'])];neg=[float(x[field]) for x in audit96 if not int(x['passed'])]
 return sum((a>b)+.5*(a==b) for a in pos for b in neg)/(len(pos)*len(neg))
report['progress_audit96']={field:auc(field) for field in ['f_progress','f_progress_strict']}
report['progress_audit96']['selected_hard8_posthoc_seed_passes']={t:sum(int(x['passed']) for x in audit96 if x['task_id']==t) for t in sorted(taskcounts['C3'])}
report['summed_task_hours']={c:sum((datetime.datetime.fromisoformat(x['completed_at_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(x['launched_at_utc'].replace('Z','+00:00'))).total_seconds()/3600 for x in metadata if x['condition']==c) for c in ['C3','C4']}
# Raw sources cannot be reconstructed from public hashes. This ledger only authenticates local public bytes.
dump('source_hashes.json',{str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(U.rglob('*')) if p.is_file() and '__pycache__' not in p.parts})
dump('independent_audit.json',report);print(json.dumps(report,indent=2))
