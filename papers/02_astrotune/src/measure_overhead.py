"""Fresh, timed retrieval pass for explicit end-to-end accounting.
These timings are remeasurement, not retroactively claimed original search overhead.
"""
import json,time
from experiment import data
from retrieval import retrieve
from eda import ROOT
rows=[];ds=data()
for q in ds[3:]:
 for mode in ('ast','numeric','text','fusion_control'):
  start=time.monotonic();r=retrieve(q,ds[:3],mode);rows.append({'design':q['id'],'mode':mode,'wall_s':time.monotonic()-start,'ranked_ids':[x['id'] for x in r]})
(ROOT/'results/retrieval_overhead.json').write_text(json.dumps(rows,indent=2))
