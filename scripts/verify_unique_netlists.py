"""Standalone stdlib recalculation of included raw-netlist gate count/depth.
This is structural metric validation, not a post-synthesis equivalence check.
"""
import hashlib,json,os
from pathlib import Path
R=Path(__file__).resolve().parents[1]/Path(os.environ.get('ASPEN_BEHAVIOR_RUN_ROOT','.'));rows=json.loads((R/'results/behavior/unique_netlist_inventory.json').read_text());assert len(rows)==14
for r in rows:
 raw=(R/r['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['representative_netlist_sha256'];m=json.loads(raw)['modules']['top'];cells=m['cells'];known={b:0 for p in m['ports'].values() if p['direction']=='input' for b in p['bits']};known.update({v:0 for v in ['0','1','x','z']});pending=list(cells.values())
 while pending:
  progress=[]
  for c in pending:
   inputs=[b for n,vs in c['connections'].items() if c['port_directions'][n]=='input' for b in vs]
   if any(b not in known for b in inputs):progress.append(c);continue
   level=1+max((known[b] for b in inputs),default=0)
   for n,vs in c['connections'].items():
    if c['port_directions'][n]=='output':
     for b in vs:known[b]=level
  assert len(progress)<len(pending),'cycle or undriven bit';pending=progress
 levels=[known[b] for p in m['ports'].values() if p['direction']=='output' for b in p['bits']];assert len(cells)==r['gates'] and max(levels)==r['depth']
print('PASS 14 raw JSON hashes and independently recomputed gate/depth pairs; no post-synthesis netlist equivalence claimed.')
