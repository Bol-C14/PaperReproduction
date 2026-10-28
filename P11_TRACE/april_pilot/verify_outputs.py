"""Read-only saved prediction/metric validation, independent of model code."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
r=Path(sys.argv[1]); rows=json.loads((r/'per_circuit.json').read_text())
summary=json.loads((r/'summary.json').read_text()); sums={}; counts={}; hashes={}
for idx,row in enumerate(rows):
 p=r/f'predictions_{idx}.npz'; d=np.load(p,allow_pickle=False)
 hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 assert int(d['mask'].sum())==row['non_pi']
 assert np.max(np.abs(d['independent']-d['inclusive']))<1e-4
 for key,v in row['metrics'].items():
  errors=np.abs(d[key]-d['target'])
  assert abs(float(errors[d['mask']].mean())-v['node_mae'])<1e-7
  if d['terminal'].any(): assert abs(float(errors[d['terminal']].mean())-v['terminal_mae'])<1e-7
  sums[key]=sums.get(key,0)+float(errors[d['mask']].astype(np.float64).sum())
  counts[key]=counts.get(key,0)+int(d['mask'].sum())
for k in sums: assert abs(sums[k]/counts[k]-summary['global_node_mae'][k])<1e-7
print(json.dumps(dict(status='pass',graphs=len(rows),non_pi_labels=counts['inclusive'],prediction_sha256=hashes),indent=2))
