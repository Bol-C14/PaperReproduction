"""Gold RTL vs mapped gate netlist; SAT-based equivalence, not PPA proxy checks."""
import json
from pathlib import Path
from eda import ROOT,run,PLATFORM
rows=[];manifest={d['id']:d for d in json.loads((ROOT/'benchmarks/manifest.json').read_text())['designs']}
# First observed successful mapping for each design/synthesis configuration.
networks={}
for path in sorted((ROOT/'results').glob('*.jsonl')):
 for line in path.read_text().splitlines():
  r=json.loads(line)
  if r['status']=='ok' and r['stage']=='synth':networks.setdefault((r['design'],r['s']),r)
for (name,s),r in networks.items():
 d=manifest[name];out=ROOT/'work/equivalence'/f'{name}_{s}';out.mkdir(parents=True,exist_ok=True)
 script=f'''read_verilog {ROOT/d['rtl']}
prep -top {d['top']} -flatten
async2sync
opt
rename {d['top']} gold
splitnets -ports
memory_map
opt
design -stash gold
read_liberty -ignore_miss_func {PLATFORM}/cells.lib
read_verilog {ROOT/r['out']}/net.v
prep -top {d['top']} -flatten
async2sync
opt
rename {d['top']} gate
splitnets -ports
memory_map
opt
design -copy-from gold -as gold gold
equiv_make gold gate equiv
hierarchy -top equiv
equiv_simple
equiv_induct -undef -seq 10
equiv_status -assert
'''
 (out/'proof.ys').write_text(script)
 try:wall=run(['yosys','-s',str(out/'proof.ys')],out/'proof.log');status='proved';error=None
 except Exception as e:status='unproved';error=str(e);wall=None
 rows.append({'design':name,'s':s,'status':status,'error':error,'wall_s':wall,'source_run':r['run'],'source_id':r['id']});print(name,s,status,flush=True)
 (ROOT/'results/equivalence.json').write_text(json.dumps(rows,indent=2))
