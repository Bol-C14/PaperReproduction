"""Supplementary role-only inference lesion; operator position stays unchanged."""
import ast,hashlib,json,sys,time,resource
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from torch import nn
ROOT=Path(__file__).resolve().parent; OUT=Path(sys.argv[3]); start=time.monotonic()
torch.set_num_threads(2)
source=(ROOT.parent/'closure/official_pm_source.py').read_text(); tree=ast.parse(source)
classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in ['MLP','PlainMLP','TRACE']]
trainer=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='TRACETrainer')
cop=next(n for n in trainer.body if isinstance(n,ast.FunctionDef) and n.name=='_cop')
ns={'torch':torch,'nn':nn}; exec(compile(ast.Module(body=classes+[cop],type_ignores=[]),'official_pm_source.py','exec'),ns)
model=ns['TRACE']().eval(); state=torch.load(sys.argv[2],map_location='cpu',weights_only=True)['state_dict']; model.load_state_dict(state,strict=True)
with torch.no_grad(): model.pos_enc.weight[1:]=model.pos_enc.weight[1].clone()
obj=SimpleNamespace(); obj._cop=lambda *a:ns['_cop'](obj,*a)
data=np.load(sys.argv[1],allow_pickle=True)['circuits'].item()
selection=json.loads((OUT/'selection.json').read_text()); previous=json.loads((OUT/'per_circuit.json').read_text()); results=[]
for idx,name in enumerate(selection['selected']):
 c=data[name]; g=SimpleNamespace(**{k:torch.tensor(c[k],dtype=torch.float32 if k=='prob' else torch.long) for k in ['x','edge_index','prob','forward_level','forward_index']}); g.prob=g.prob.reshape(-1)
 with torch.no_grad():
  shift=model.pred_prob(model(g)); targets,cov,_=obj._cop(g.edge_index,g.prob,g.x)
  # Reorder operand tokens within each target, preserving all source identities.
  swapped=SimpleNamespace(**vars(g)); swapped.edge_index=g.edge_index.clone()
  for target in torch.unique(g.edge_index[1]):
   cols=torch.where(g.edge_index[1]==target)[0]; swapped.edge_index[0,cols]=g.edge_index[0,cols.flip(0)]
  reverse_shift=model.pred_prob(model(swapped))
  prediction=torch.zeros_like(g.prob); prediction[g.forward_level==0]=g.prob[g.forward_level==0]
  for level in range(1,int(g.forward_level.max())+1):
   edges=g.edge_index[:,g.forward_level[g.edge_index[1]]==level]
   if edges.numel():
    unique,_,local=obj._cop(edges,prediction,g.x); prediction[unique]=local+shift[unique,0]
 saved=np.load(OUT/f'predictions_{idx}.npz',allow_pickle=False); mask=g.forward_level>0
 row=dict(name=name,node_mae=float((prediction[mask]-g.prob[mask]).abs().mean()),residual_mae=float((shift[targets,0]-cov).abs().mean()),residual_mean_abs_change=float((shift[mask]-torch.from_numpy(saved['official_shift'])[mask]).abs().mean()),operand_reverse_shift_max_abs=float((shift[mask]-reverse_shift[mask]).abs().max()),operator_position_preserved=bool(torch.equal(model.pos_enc.weight[0],state['pos_enc.weight'][0])))
 assert row['operator_position_preserved']; assert row['operand_reverse_shift_max_abs']<1e-5
 np.savez_compressed(OUT/f'operand_role_{idx}.npz',prediction=prediction.numpy(),shift=shift.numpy(),reverse_shift=reverse_shift.numpy())
 results.append(row); print(json.dumps(row),flush=True)
(OUT/'OPERAND_ROLE.json').write_text(json.dumps(dict(status='completed',rows=results,wall_s=time.monotonic()-start,cpu_s=time.process_time(),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),interpretation='post-hoc operand position collapse; fixed operator position; not retrained ablation'),indent=2)+'\n')
