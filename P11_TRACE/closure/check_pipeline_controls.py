"""Full prediction rename/control replay on saved main weights and original asset; no training."""
import copy
import json
from pathlib import Path
import torch
import run_closure as c

R=Path(__file__).resolve().parent
torch.set_num_threads(1);torch.set_num_interop_threads(1)
ns=c.load_official();data=json.loads((R/'frozen_families.json').read_text())['rows']
results=[]
for checkpoint in sorted((R/'weights').glob('*_adapt.pt')):
    seed,arm,*family_parts=checkpoint.stem.split('_')
    family='_'.join(family_parts[:-1])
    rows=[r for r in data if r['family']==family and r['split']=='query'][:8]
    g=c.batch(rows);model=c.make_model(ns,int(seed))
    model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True),strict=True);model.eval()
    with torch.no_grad():
        pred,_=c.predict(model,g,arm)
        permutation=torch.randperm(len(g.ops),generator=torch.Generator().manual_seed(74))
        inv=torch.argsort(permutation);h=copy.copy(g)
        for name in ['x','prob','target','forward_level','residual','local_teacher']:
            setattr(h,name,getattr(g,name)[permutation])
        edge=inv[g.edge_index];order=torch.argsort(edge[1]*8+g.edge_pos)
        h.edge_index=edge[:,order];h.forward_index=torch.arange(len(g.ops));h.edge_pos=g.edge_pos[order]
        h.plan=[(level,op,inv[idx],inv[src]) for level,op,idx,src in g.plan]
        renamed,_=c.predict(model,h,arm)
        delta=float((pred-renamed[inv]).abs().max());assert delta<1e-5
        # Numeric PI/input transport, then every dependent level rebuilt.
    results.append(dict(checkpoint=checkpoint.name,prediction_rename_max_abs=delta))
assert len(results)==24
# Train-adapt/predict correspondence independently reloads a saved seed and compares saved outputs.
checkpoint=R/'weights/2026_fsl_ripple_carry_adapt.pt'
model=c.make_model(ns,2026);model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True));model.eval()
rows=[r for r in data if r['family']=='ripple_carry' and r['split']=='query'];g=c.batch(rows)
with torch.no_grad():p,_=c.predict(model,g,'fsl')
saved=json.loads((R/'predictions/2026_fsl_ripple_carry_adapt.json').read_text())
flat=torch.tensor([x for row in saved for x in row['prediction']]);reload_delta=float((p-flat).abs().max());assert reload_delta<1e-6
report=dict(status='pass',main_adapted_checkpoints=results,reload_prediction_max_abs=reload_delta,
    note='Transfer states had raw rename checks during execution; this extra complete-recursion replay covers all24 saved main adapted states')
(R/'PIPELINE_CONTROLS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status='pass',checkpoints=24,max_prediction_rename_delta=max(x['prediction_rename_max_abs'] for x in results),reload_delta=reload_delta)))
