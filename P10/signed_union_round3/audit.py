"""Independent domain calibration and post-selection generic synthesis audit."""
import json,random,time,subprocess,hashlib,sys,importlib.metadata,datetime
from pathlib import Path
from union_domain import wrap,unary,signed_range,norm,meet
R=Path('/home/shugu/work/paper-reproduction-april-20261028');OUT=R/'results/rover/signed_union_round3';ROOT=Path(__file__).resolve().parent
Y=R/'envs/rover/bin/yowasp-yosys'
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def inside(x,rs):return any(a<=x<=b for a,b in rs)
if (OUT/'audit.json').exists():raise RuntimeError('Refuse audit overwrite')
start=time.monotonic();checks=0;rng=random.Random(20261028)
for w in range(1,9):
 m=1<<w;h=m//2
 for k in range(-h,h):
  rs=signed_range(-h,k-1,w)
  for x in range(m):
   signed=x if x<h else x-m
   assert inside(x,rs)==(signed<k);checks+=1
 for _ in range(100):
  a,b=sorted([rng.randrange(m),rng.randrange(m)]);c,d=sorted([rng.randrange(m),rng.randrange(m)])
  for op in ['Abs','Neg']:
   rs=unary(((a,b),),w,op)
   for x in range(a,b+1):
    sx=x if x<h else x-m;v=abs(sx)%m if op=='Abs' else -x%m
    assert inside(v,rs);checks+=1
  for op in ['Add','Mul']:
   rs=wrap(a+c,b+d,w) if op=='Add' else wrap(a*c,b*d,w)
   for x in range(a,b+1):
    for y in range(c,d+1):
     v=(x+y)%m if op=='Add' else (x*y)%m
     assert inside(v,rs);checks+=1
audit={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'domain_containment_checks':checks,'domain_calibration':'100 seeded interval pairs per width1..8; complete values inside each pair; all signed thresholds and bit encodings; no sampled checks substitute circuit proofs','synthesis':[]}
summary=json.loads((OUT/'summary.json').read_text());seen={}
for row in summary['rows']:
 if not row.get('pass'):continue
 for i,v in enumerate(row['variants']):
  d=OUT/row['key']/f'variant{i}'
  for f,top in [('original.v','original'),('candidate.v','candidate')]:
   source=(d/f).read_bytes();sha=hashlib.sha256(source).hexdigest()
   if sha not in seen:
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
audit['versions']={k:importlib.metadata.version(k) for k in ['egglog','z3-solver','yowasp-yosys']}
write(OUT/'audit.json',audit);print(json.dumps({k:v for k,v in audit.items() if k!='synthesis'},indent=2))
