"""Bounded alternate-tool MCM pilot; not ASPEN/ROVER or technology PPA."""
import hashlib,itertools,json,os,random,subprocess,time
from pathlib import Path
from z3 import BitVec,BitVecVal,Solver,unsat,Or
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
cfg=json.loads(Path('configs/pilot.json').read_text());out=Path('results/netlists');out.mkdir(exist_ok=True)
rtl=Path('results/rtl');rtl.mkdir(exist_ok=True)
X=('x',)
def node(op,*args):return (op,*args)
def binary(c):
 ts=[X if k==0 else node('shl',X,k) for k in range(c.bit_length()) if c>>k&1]
 while len(ts)>1: ts=[node('add',ts[i],ts[i+1]) if i+1<len(ts) else ts[i] for i in range(0,len(ts),2)]
 return ts[0]
def signed(c):
 if c==1:return X
 if c%2==0:return node('shl',signed(c//2),1)
 if c%4==3:return node('sub',node('shl',signed((c+1)//2),1),X)
 return node('add',node('shl',signed(c//2),1),X)
def partial(c):return node('add',node('shl',node('mul',c//2,X),1),X) if c%2 else node('shl',node('mul',c//2,X),1)
def emit(e,w):
 op=e[0]
 if op=='x':return 'x'
 if op=='mul':return f"({w}'d{e[1]} * {emit(e[2],w)})"
 if op=='shl':return f'({emit(e[1],w)} << {e[2]})'
 return f'({emit(e[1],w)} {"+" if op=="add" else "-"} {emit(e[2],w)})'
def zexpr(e,x,w):
 op=e[0]
 if op=='x':return x
 if op=='mul':return e[1]*zexpr(e[2],x,w)
 if op=='shl':return BitVecVal(0,w) if e[2]>=w else zexpr(e[1],x,w)<<e[2]
 a,b=zexpr(e[1],x,w),zexpr(e[2],x,w);return a+b if op=='add' else a-b
def tree_depth(e):
 return 0 if e[0]=='x' else 1+max([tree_depth(v) for v in e[1:] if isinstance(v,tuple)] or [0])
def features(es):
 seen=set();counts=dict(mul=0,add=0,sub=0,shl=0)
 def walk(e):
  if e in seen:return tree_depth(e)
  seen.add(e);op=e[0]
  if op=='x':return 0
  counts[op]+=1
  children=[v for v in e[1:] if isinstance(v,tuple)]
  return 1+max([walk(v) for v in children] or [0])
 depth=max(walk(e) for e in es)
 return [counts[k] for k in ['mul','add','sub','shl']]+[depth]
def metrics(path):
 mod=json.loads(path.read_text())['modules']['top'];cells=mod['cells'];depth={b:0 for p in mod['ports'].values() if p['direction']=='input' for b in p['bits']};depth.update({'0':0,'1':0,'x':0,'z':0});pending=list(cells.values())
 while pending:
  nxt=[]
  for c in pending:
   ins=[b for p,bs in c['connections'].items() if c['port_directions'][p]=='input' for b in bs]
   if not all(b in depth for b in ins):nxt.append(c);continue
   d=1+max([depth[b] for b in ins] or [0])
   for p,bs in c['connections'].items():
    if c['port_directions'][p]=='output':depth.update({b:d for b in bs})
  if len(nxt)==len(pending):raise RuntimeError('cycle/unresolved bit')
  pending=nxt
 return len(cells),max(depth[b] for p in mod['ports'].values() if p['direction']=='output' for b in p['bits'])
rows=[];start=time.perf_counter()
for w,cs in itertools.product(cfg['widths'],cfg['constants']):
 variants=[[node('mul',c,X),binary(c),signed(c),partial(c)] for c in cs]
 choices=list(itertools.product(range(4),repeat=len(cs)));random.Random(42).shuffle(choices)
 choices=[tuple([k]*len(cs)) for k in range(4)]+choices[:8]
 seen=set()
 for choice in choices:
  es=tuple(variants[i][j] for i,j in enumerate(choice))
  if es in seen:continue
  seen.add(es);ident=f'mcm_{"_".join(map(str,cs))}_w{w}_{len(seen)-1:02}'
  x=BitVec('x',w);s=Solver();s.set(timeout=5000);s.add(Or(*[zexpr(e,x,w)!=c*x for e,c in zip(es,cs)]));proof=str(s.check());assert proof=='unsat'
  text=f'module top(input [{w-1}:0] x, '+', '.join(f'output [{w-1}:0] y{i}' for i in range(len(cs)))+');\n'+'\n'.join(f'assign y{i} = {emit(e,w)};' for i,e in enumerate(es))+'\nendmodule\n'
  src=rtl/f'{ident}.v';src.write_text(text);dest=out/f'{ident}.json'
  command=[str(ROOT/'.venv/bin/yowasp-yosys'),'-Q','-T','-p',f'read_verilog {src}; synth -top top -noabc; write_json {dest}']
  t=time.perf_counter();p=subprocess.run(command,text=True,capture_output=True,timeout=cfg['synthesis_timeout_seconds'],env={**os.environ,'XDG_CACHE_HOME':str(ROOT/'.cache')});dt=time.perf_counter()-t
  Path(f'logs/{ident}.log').write_text(p.stdout+p.stderr);assert p.returncode==0 and dest.exists(),ident
  gates,depth=metrics(dest);row=dict(id=ident,width=w,constants=cs,choice=choice,features=features(es),gate_count=gates,logic_depth=depth,seconds=dt,proof=proof,rtl_sha256=hashlib.sha256(text.encode()).hexdigest(),netlist_sha256=hashlib.sha256(dest.read_bytes()).hexdigest());rows.append(row)
  print(json.dumps(row),flush=True)
Path('results/pilot_candidates.json').write_text(json.dumps(rows,indent=2))
Path('results/pilot_execution.json').write_text(json.dumps(dict(seconds=time.perf_counter()-start,synthesis_calls=len(rows),z3_checks=len(rows),llm_calls=0,cost_usd=0),indent=2))
