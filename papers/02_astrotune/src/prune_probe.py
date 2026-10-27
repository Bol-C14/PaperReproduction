"""One bounded, post-main branch-coverage run on real EDA. NOT a performance arm.
Default5% never fired because layout QoR has a100 offset. Probe uses a narrower
threshold prospectively; its result must not be pooled with predeclared arms.
"""
import json
from experiment import data,Search
from retrieval import retrieve
from eda import ROOT
q=next(d for d in data() if d['id']=='div_16bit');donor=retrieve(q,data()[:3],'ast')[0]['id'];db={x['id']:x['config'] for x in json.loads((ROOT/'results/legacy_db.json').read_text())}
s=Search(q,'ast_tournament_prune_probe',0,db[donor],18);s.prune_ratio=1.00001;r=s.run();r['not_performance_arm']=True;r['probe_prune_ratio']=s.prune_ratio
(ROOT/'results'/f'{r["run"]}.summary.json').write_text(json.dumps(r,indent=2));print(r['best_qor'],r['events'])
