"""Bounded v2 correction:2 existing targets,2 seeds,5 arms,8 calls/arm,<=3 synth.
Plus true62-call random baselines matching full54-call history+8 online calls.
All EDA fresh. No response cache/replay; frozen donor DB is retained and charged.
"""
import json,time,itertools,hashlib
from experiment import Search,data
from retrieval import retrieve
from eda import ROOT
R=ROOT/'results';ds=data();db=json.loads((R/'legacy_db.json').read_text());config={x['id']:x['config'] for x in db};donor_hash=hashlib.sha256((R/'legacy_db.json').read_bytes()).hexdigest();plan=[]
for q in [d for d in ds if d['id'] in ('multi_pipe_8bit','div_16bit')]:
 t=time.monotonic();rank=retrieve(q,ds[:3],'ast');retrieval_s=time.monotonic()-t;warm=config[rank[0]['id']]
 for method,seed in itertools.product(['random','gp_single','ast_single','ast_gp_all','ast_tournament'],(0,1)):
  name=f'v2pilot_{q["id"]}_{method}_{seed}';dest=R/f'{name}.summary.json'
  if dest.exists():continue
  search=Search(q,method,seed,warm if method.startswith('ast') else (0,0),8,runid=name);search.max_synth=3
  result=search.run();assert result['unique_synth']<=3 and result['calls']==8
  result.update(stratum='gp_fix_pilot',retrieval_mode='ast' if method.startswith('ast') else None,serving_db_sha256=donor_hash,history_cost_charged=54 if method.startswith('ast') else 0,eda_response_cache_hits=0,retrieval_ranking_reused=method.startswith('ast'),retrieval_preparation_wall_s=retrieval_s if method.startswith('ast') else 0)
  dest.write_text(json.dumps(result,indent=2));print(name,result['calls'],result['unique_synth'],result['best_qor'],flush=True)
 for seed in (0,1):
  name=f'v2pilot_{q["id"]}_random_inclusive_{seed}';dest=R/f'{name}.summary.json'
  if dest.exists():continue
  result=Search(q,'random',seed,(0,0),62,runid=name).run();result.update(method='random_inclusive',stratum='gp_fix_pilot',history_cost_charged=0,eda_response_cache_hits=0);dest.write_text(json.dumps(result,indent=2));print(name,result['calls'],result['best_qor'],flush=True)
assert hashlib.sha256((R/'legacy_db.json').read_bytes()).hexdigest()==donor_hash
