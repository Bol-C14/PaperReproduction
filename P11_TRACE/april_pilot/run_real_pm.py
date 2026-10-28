"""Frozen real PM checkpoint pilot. No optimization; see PROTOCOL.md."""
import ast, copy, hashlib, json, os, resource, sys, time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from torch import nn

ROOT=Path(__file__).resolve().parent
OUT=Path(sys.argv[3]); OUT.mkdir(parents=True,exist_ok=True)
start=time.monotonic(); torch.set_num_threads(2); torch.manual_seed(208)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
assert sha(sys.argv[1])=='6a05e443aeb824b0b47f53e8355572fbafc3aa18f400540ce0306a3791e6ed36'
assert sha(sys.argv[2])=='19fe1e95857072e5eb838802ee21260ffe48345df85785f9f6ddd0e784cad7c0'
source=(ROOT.parent/'closure/official_pm_source.py').read_text()
tree=ast.parse(source)
ns={'torch':torch,'nn':nn}
classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in ['MLP','PlainMLP','TRACE']]
trainer=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='TRACETrainer')
methods=[n for n in trainer.body if isinstance(n,ast.FunctionDef) and n.name in ['_cop','_cop_with_cov']]
exec(compile(ast.Module(body=classes+methods,type_ignores=[]),'official_pm_source.py','exec'),ns)
corrected=copy.deepcopy(next(n for n in methods if n.name=='_cop_with_cov'))
corrected.name='inclusive'
for n in ast.walk(corrected):
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='max_level' for t in n.targets):
  n.value=ast.BinOp(left=n.value,op=ast.Add(),right=ast.Constant(value=1))
exec(compile(ast.fix_missing_locations(ast.Module(body=[corrected],type_ignores=[])),'inclusive_patch','exec'),ns)
lesion=copy.deepcopy(next(n for n in classes if n.name=='TRACE'))
lesion.name='TRACEFrozen'
forward=next(n for n in lesion.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
# Snapshot after PI initialization; all predecessor tokens use this snapshot.
forward.body.insert(3,ast.parse('initial_h = h.clone()').body[0])
for n in ast.walk(forward):
 if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='h' and isinstance(n.slice,ast.Name) and n.slice.id=='index_matrix': n.value.id='initial_h'
exec(compile(ast.fix_missing_locations(ast.Module(body=[lesion],type_ignores=[])),'frozen_predecessor_lesion','exec'),ns)
model=ns['TRACE']().eval()
ck=torch.load(sys.argv[2],map_location='cpu',weights_only=True)
state=ck.get('state_dict',ck); model.load_state_dict(state,strict=True)
frozen=ns['TRACEFrozen']().eval(); frozen.load_state_dict(state,strict=True)
no_pos=copy.deepcopy(model)
with torch.no_grad(): no_pos.pos_enc.weight.zero_()
obj=SimpleNamespace(_cop=ns['_cop'])
# Bind the original local function exactly as the trainer does.
obj._cop=lambda *a: ns['_cop'](obj,*a)
circuits=np.load(sys.argv[1],allow_pickle=True)['circuits'].item()
names=list(circuits); perm=torch.randperm(len(names),generator=torch.Generator().manual_seed(208)).tolist()
valid=[names[i] for i in perm[int(.9*len(names)):]]
selected=[]; skipped=[]
for name in valid[:32]:
 n=len(circuits[name]['x'])
 if n>4096: skipped.append(dict(name=str(name),nodes=n,reason='frozen node cap')); continue
 selected.append(name)
 if len(selected)==8: break
save('selection.json',dict(total=len(names),validation=len(valid),selected=[str(x) for x in selected],skipped=skipped,seed=208,split=.9))
assert selected
rows=[]; errors=[]; all_abs={}
for idx,name in enumerate(selected):
 if time.monotonic()-start>900: raise TimeoutError('frozen 15min limit')
 c=circuits[name]; n=len(c['x'])
 g=SimpleNamespace(**{k:torch.tensor(c[k],dtype=torch.float32 if k=='prob' else torch.long) for k in ['x','edge_index','prob','forward_level','forward_index','backward_level','backward_index']})
 g.prob=g.prob.reshape(-1)
 # The pinned source indexes levels by node ID and expects edges grouped by target.
 assert g.x.shape==(n,64)
 assert torch.equal(g.forward_index,torch.arange(n)), 'forward_index identity assumption fails'
 assert bool(torch.all(g.edge_index[1,1:]>=g.edge_index[1,:-1])), 'stored target grouping fails'
 assert bool(torch.all(g.forward_level[g.edge_index[0]]<g.forward_level[g.edge_index[1]]))
 counts=torch.bincount(g.edge_index[1],minlength=n); assert int(counts.max())<=6
 mask=g.forward_level>0
 terminal=torch.ones(n,dtype=torch.bool); terminal[g.edge_index[0]]=False; terminal &=mask
 with torch.no_grad():
  shifts={key:m.pred_prob(m(g)) for key,m in [('official',model),('no_position',no_pos),('frozen_predecessor',frozen)]}
  pred={'original':ns['_cop_with_cov'](obj,g,shifts['official']),
        'inclusive':ns['inclusive'](obj,g,shifts['official']),
        'local_only':ns['inclusive'](obj,g,torch.zeros_like(shifts['official'])),
        'no_position':ns['inclusive'](obj,g,shifts['no_position']),
        'frozen_predecessor':ns['inclusive'](obj,g,shifts['frozen_predecessor'])}
  targets,cov,_=obj._cop(g.edge_index,g.prob,g.x)
  # Independent scalar, full truth-pattern enumeration; no source _cop calls.
  independent=np.array(g.prob.tolist(),dtype=np.float64)
  independent[mask.numpy()]=0
  incoming=[[] for _ in range(n)]
  for s,t in g.edge_index.T.tolist():incoming[t].append(s)
  for level in range(1,int(g.forward_level.max())+1):
   for target in torch.where(g.forward_level==level)[0].tolist():
    ins=incoming[target]; pads=[-1]*(6-len(ins))+ins
    probabilities=independent[pads]
    local=0.
    for pattern in range(64):
     weight=1.
     for j,p in enumerate(probabilities): weight*=p if ((pattern>>(5-j))&1) else (1-p)
     # Official PM features store the truth table in descending pattern order.
     local+=float(g.x[target,63-pattern])*weight
    independent[target]=local+float(shifts['official'][target,0])
  recurrence_error=float(np.max(np.abs(independent-pred['inclusive'].numpy())))
  assert recurrence_error<1e-4, recurrence_error
 row=dict(name=str(name),nodes=n,non_pi=int(mask.sum()),terminals=int(terminal.sum()),depth=int(g.forward_level.max()),recurrence_error=recurrence_error,metrics={},residual={})
 for key,p in pred.items():
  absolute=(p-g.prob).abs()
  row['metrics'][key]=dict(node_mae=float(absolute[mask].mean()),terminal_mae=float(absolute[terminal].mean()) if terminal.any() else None,min=float(p.min()),max=float(p.max()),outside=int(((p<0)|(p>1)).sum()))
  all_abs.setdefault(key,[]).extend(absolute[mask].tolist())
 for key,s in shifts.items():
  row['residual'][key]=dict(mae=float((s[targets,0]-cov).abs().mean()),mean_abs_change=float((s[mask]-shifts['official'][mask]).abs().mean()))
 np.savez_compressed(OUT/f'predictions_{idx}.npz',target=g.prob.numpy(),mask=mask.numpy(),terminal=terminal.numpy(),independent=independent,**{k:p.numpy() for k,p in pred.items()},**{k+'_shift':p.numpy() for k,p in shifts.items()})
 rows.append(row); save('per_circuit.json',rows); print(json.dumps(row),flush=True)
save('summary.json',dict(status='completed',graphs=len(rows),global_node_mae={k:float(np.mean(v)) for k,v in all_abs.items()},wall_s=time.monotonic()-start,cpu_s=time.process_time(),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,torch=torch.__version__,numpy=np.__version__,python=sys.version,source_sha256=hashlib.sha256(source.encode()).hexdigest(),script_sha256=sha(__file__),protocol_sha256=sha(ROOT/'PROTOCOL.md'),checkpoint_state_entries=len(state),paid_usd=0,optimizer_updates=0))
