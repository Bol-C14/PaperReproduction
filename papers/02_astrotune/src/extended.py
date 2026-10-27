"""Prospective harder case added after initial small cases showed flat objective.
Separate stress stratum; no replacement or exclusion of initial null results.
"""
import json,itertools,time
from experiment import data,Search
from retrieval import retrieve
from eda import ROOT,EDA
q=data()[-1];assert q['id']=='div_16bit'
ranks=retrieve(q,data()[:3],'ast');db={x['id']:x['config'] for x in json.loads((ROOT/'results/legacy_db.json').read_text())};warm=db[ranks[0]['id']]
(ROOT/'results/extended_rankings.json').write_text(json.dumps(ranks,indent=2))
for method,seed in itertools.product(['random','gp_single','ast_tournament','ast_tournament_no_prune'],(0,1,2)):
 name=f'{q["id"]}_{method}_{seed}'
 if (ROOT/'results'/f'{name}.summary.json').exists():continue
 r=Search(q,method,seed,warm if method.startswith('ast') else (0,0),18).run();print(name,r['best_qor'],flush=True)
