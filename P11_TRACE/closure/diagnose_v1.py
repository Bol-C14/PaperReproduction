"""Retrospective oracle diagnosis of preserved v1 weights. No training/tuning."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import torch
from torch import nn

R=Path(__file__).resolve().parent
P=R.parent/'pilot';sys.path.insert(0,str(P))
from vendor.aig.trace_encoder_impl import TRACE
from vendor.aig.mlp import MLP
from vendor.aig.cov2prob import cov2prob

torch.set_num_threads(1);torch.set_num_interop_threads(1)
rows=[r for r in json.loads((P/'frozen_circuits.json').read_text())['samples'] if r['split']=='test']
gates=[];levels=[];edges=[];target=[]
for row in rows:
    offset=len(gates);local=[]
    for i,(op,src) in enumerate(row['nodes']):
        gates.append(dict(PI=0,AND=1,NOT=2)[op]);local.append(0 if not src else 1+max(local[j] for j in src))
        edges.extend([j+offset,i+offset] for j in src)
    levels.extend(local);target.extend(row['global_prob'])
g=SimpleNamespace(gate=torch.tensor(gates),edge_index=torch.tensor(edges).t().contiguous(),
    forward_level=torch.tensor(levels),forward_index=torch.arange(len(gates)),prob=torch.tensor(target))
outputs=torch.arange(7,len(gates),8)

class Pilot(nn.Module):
    def __init__(self):
        super().__init__();self.encoder=TRACE(SimpleNamespace(),num_rounds=1,dim_hidden=32)
        self.head=MLP(32,16,1,num_layer=3)
    def forward(self,g):return self.head(self.encoder(g)).squeeze(-1)

result={}
for arm in ['direct','residual']:
    model=Pilot();model.load_state_dict(torch.load(P/f'{arm}_pilot_weights.pt',map_location='cpu',weights_only=True),strict=True);model.eval()
    with torch.no_grad():
        raw=model(g);teacher=torch.zeros_like(g.prob)
        if arm=='direct':pred=raw.clamp(0,1);teacher=pred
        else:
            raw=raw.clamp(-1,1);pred=cov2prob(g,raw)
            teacher[g.gate==0]=g.prob[g.gate==0]
            for row_index,row in enumerate(rows):
                for i,(op,src) in enumerate(row['nodes']):
                    idx=row_index*8+i
                    if op=='AND':teacher[idx]=g.prob[row_index*8+src[0]]*g.prob[row_index*8+src[1]]+raw[idx]
                    elif op=='NOT':teacher[idx]=1-g.prob[row_index*8+src[0]]
        saved=torch.tensor(json.loads((P/f'{arm}_predictions.json').read_text())['prediction'])
        reload_error=float((saved-pred).abs().max());assert reload_error<1e-6
        error=(pred-g.prob).abs();oracle_error=(teacher-g.prob).abs()
        stats=dict(reload_prediction_max_abs=reload_error,node_mae=float(error[g.gate!=0].mean()),
            output_mae=float(error[outputs].mean()),teacher_output_mae=float(oracle_error[outputs].mean()),
            recursive_teacher_output_gap=float((pred[outputs]-teacher[outputs]).abs().mean()),
            by_gate={name:dict(count=int((g.gate==idx).sum()),mae=float(error[g.gate==idx].mean()),
                teacher_mae=float(oracle_error[g.gate==idx].mean())) for idx,name in [(1,'AND'),(2,'NOT')]},
            by_level={str(level):dict(count=int((g.forward_level==level).sum()),
               mae=float(error[g.forward_level==level].mean()),teacher_mae=float(oracle_error[g.forward_level==level].mean()))
               for level in sorted(set(levels)) if level>0})
        result[arm]=stats
(R/'V1_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
