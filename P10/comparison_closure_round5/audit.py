"""Post-selection synthesis only; at most two selected outputs per arm/circuit."""
import json,time,subprocess,hashlib,datetime
from pathlib import Path
R=Path('/home/shugu/work/paper-reproduction-april-20261028');OUT=R/'results/rover/comparison_closure_round5_attempt1'
Y=R/'envs/rover/bin/yowasp-yosys'
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
if (OUT/'audit.json').exists():raise RuntimeError('Refuse audit overwrite')
start=time.monotonic()
audit={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'synthesis':[]}
summary=json.loads((OUT/'summary.json').read_text());seen={}
for row in summary['rows']:
 if not row.get('pass'):raise RuntimeError('Refuse synthesis after failed experiment row')
 for i,v in enumerate(row['variants']):
  d=OUT/row['key']/f'variant{i}'
  for f,top in [('original.v','original'),('candidate.v','candidate')]:
   source=(d/f).read_bytes();sha=hashlib.sha256(source).hexdigest()
   if sha not in seen:
    if len(seen)>=3:raise RuntimeError('3 synthesis hard budget reached')
    dest=OUT/'synthesis'/sha[:16];dest.mkdir(parents=True)
    (dest/'input.v').write_bytes(source)
    (dest/'synth.ys').write_text(f'read_verilog input.v\nsynth -top {top} -noabc\nwrite_json netlist.json\nstat\n')
    cmd=[str(Y),'-Q','-T','-s','synth.ys'];t=time.monotonic();p=subprocess.run(cmd,cwd=dest,capture_output=True,text=True,timeout=45)
    (dest/'stdout.log').write_text(p.stdout);(dest/'stderr.log').write_text(p.stderr)
    result={'source_sha256':sha,'path':str(dest),'exit':p.returncode,'wall_s':time.monotonic()-t,'command':cmd}
    if p.returncode==0:
     net=json.loads((dest/'netlist.json').read_text())['modules'][top];cells=net['cells'];types={}
     for cell in cells.values():types[cell['type']]=types.get(cell['type'],0)+1
     # Independent longest gate path from JSON connectivity; combinational only.
     levels={bit:0 for port in net['ports'].values() if port['direction']=='input' for bit in port['bits']};levels.update({'0':0,'1':0,'x':0,'z':0});pending=list(cells.values())
     while pending:
      remain=[]
      for cell in pending:
       ins=[bit for pn,bits in cell['connections'].items() if cell['port_directions'][pn]=='input' for bit in bits]
       if all(bit in levels for bit in ins):
        dep=1+max([levels[bit] for bit in ins] or [0])
        for pn,bits in cell['connections'].items():
         if cell['port_directions'][pn]=='output':
          for bit in bits:levels[bit]=max(levels.get(bit,0),dep)
       else:remain.append(cell)
      if len(remain)==len(pending):raise RuntimeError('Unresolved netlist dependency')
      pending=remain
     result.update(gates=len(cells),types=types,depth=max(levels[b] for p in net['ports'].values() if p['direction']=='output' for b in p['bits']))
    seen[sha]=result
   audit['synthesis'].append({'key':row['key'],'variant':i,'source':f,**seen[sha]})

audit['unique_synthesis_calls']=len(seen);audit['wall_s']=time.monotonic()-start
audit['selected_slots_by_arm']={a:sum(len(r['variants']) for r in summary['rows'] if r['arm']==a) for a in ['fold_off','fold_on']}
audit['pass']=all(r['exit']==0 for r in seen.values())
write(OUT/'audit.json',audit)
print(json.dumps({k:v for k,v in audit.items() if k!='synthesis'},indent=2))
raise SystemExit(0 if audit['pass'] else 1)
