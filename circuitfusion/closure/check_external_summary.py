"""Correct an external-only summary in evaluation, without changing training.
The open counter has no data operands, so its operand-swap sentence is inapplicable.
All learned checkpoints and primary synthetic-parent results are preserved.
"""
import json,re,time
from pathlib import Path
import torch
from train import Data,Model
ROOT=Path(__file__).resolve().parent

def main():
    start=time.monotonic();torch.set_num_threads(2);records=json.loads((ROOT/'manifest.json').read_text());external=[r for r in records if r['external']];assert len(external)==1;r=external[0];before=r['summary'];r['summary']=before.replace(' Data operand exchange is asymmetric.','');assert r['summary']!=before;r['summary_tokens']=re.findall('[a-z]+',r['summary'].lower());ds=Data(records);rows=json.loads((ROOT/'results_v1_1/metrics.json').read_text())['runs'];out=[]
    for row in rows:
        arm=row['arm'];seed=row['seed'];model=Model(ds);model.load_state_dict(torch.load(ROOT/'results_v1_1'/f'{arm}_seed{seed}.pt',map_location='cpu',weights_only=True));model.eval()
        with torch.no_grad():
            idx=ds.test;batch=ds.rtl(idx)
            if arm=='shuffled_edges':
                # Match original evaluation: rewiring is indexed by global batch position.
                allidx=torch.arange(len(ds.rs));full=ds.rtl(allidx);full=(full[0],full[1],ds.rewired(full[2],seed+9000));z=model.rtl(full,arm)[0][idx]
            else:z=model.rtl(batch,arm)[0]
            net=model.net(ds.net(idx));ranking=(z@net.T).argsort(1,descending=True)[-1];target=len(idx)-1;out.append({'seed':seed,'arm':arm,'recall_at_1':int(ranking[0]==target),'recall_at_5':int((ranking[:5]==target).any())})
    result={'reason':'external counter has no data operands; removed inapplicable exchange-asymmetry sentence','original_summary':before,'corrected_summary':r['summary'],'training_changed':False,'primary_synthetic_results_changed':False,'candidate_pool_size':len(ds.test),'rows':out,'wall_seconds':time.monotonic()-start};(ROOT/'results_v1_1/external_summary_corrected.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
