"""Run only AFTER main searches: inclusive budget, measured transfer and repeatability."""
import json,time
from experiment import data,Search
from eda import ROOT,EDA
from qor import layout

def main():
 ds=data();db=json.loads((ROOT/'results/legacy_db.json').read_text())
 # Frozen donor preparation costs 3*18=54 calls. Charge that entire cost to each retrieval use.
 # Give no-retrieval random exactly 18+54=72 online calls; no offline objective matrix.
 for d in ds[3:]:
  for seed in (0,1,2):
   name=f'{d["id"]}_random_inclusive_{seed}';p=ROOT/'results'/f'{name}.summary.json'
   if p.exists():continue
   r=Search(d,'random',seed,(0,0),72,runid=name).run();r['method']='random_inclusive';p.write_text(json.dumps(r,indent=2));print(name,r['best_qor'],flush=True)
 # Every donor's *selected* config measured on every target only after all searches.
 matrix=[]
 for d in ds[3:]:
  e=EDA('transfer_'+d['id']);a=e.evaluate(d,0,label='transfer_reference');ref=e.evaluate(d,0,0,a,label='transfer_reference')
  for donor in db:
   s,p=donor['config'];a=e.evaluate(d,s,label='posthoc_transfer');r=e.evaluate(d,s,p,a,label='posthoc_transfer')
   matrix.append({'target':d['id'],'donor':donor['id'],'s':s,'p':p,'qor':layout(r['area'],r['power'],r['slack'],ref),'reference':ref,'result':r})
 (ROOT/'results/transfer_matrix.json').write_text(json.dumps(matrix,indent=2))
 # Determinism is two extra physical tool executions, NOT extra random seeds.
 repeats=[]
 for d in ds[3:]:
  e=EDA('repeat_'+d['id'])
  for repeat in (0,1):
   a=e.evaluate(d,0,label='determinism');r=e.evaluate(d,0,0,a,label='determinism');repeats.append(r)
 (ROOT/'results/determinism.json').write_text(json.dumps(repeats,indent=2))
if __name__=='__main__':main()
