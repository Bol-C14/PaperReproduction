"""Bounded new mechanism round; no model/API calls, no offline PPA oracle."""
import argparse,copy,gzip,hashlib,heapq,json,math,os,random,re,subprocess,time
from pathlib import Path
from z3 import BitVec,Or,Solver
from behavior_engine import build,extract,initial_costs,emit,zexpr,reference
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
C=json.loads(Path('configs/attribution_round.json').read_text());O=Path('results/attribution_round');L=Path('logs/attribution_round');OPS={'Add','Sub','Mul','Shl'}
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2))
def sha(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
def graph_for(name):return build(name,'expanded','constants_only',C['rounds'],C['node_limit'])
def tagged(graph,ex,w):
 nodes=graph['nodes'];choices=ex['choices'];lines=[];line_nodes={};memo={};terms={};variables=set()
 def visit(cl):
  if cl in memo:return memo[cl],terms[cl]
  nid=choices[cl];n=nodes[nid];children=[visit(nodes[c]['eclass']) for c in n['children']];op=n['op']
  if not children:v=json.loads(op) if op.startswith('"') else int(op);memo[cl]=v;terms[cl]=v;return v,v
  vals=[v for v,t in children];ts=[t for v,t in children];t=(op,*ts)
  if op=='Var':v=vals[0];variables.add(v)
  elif op=='Num':v=f"{w}'d{vals[0]%(1<<w)}"
  else:
   v='n_'+hashlib.sha256(nid.encode()).hexdigest()[:12]
   rhs=f'({vals[0]} << {vals[1]})' if op=='Shl' else f'({vals[0]} '+{'Mul':'*','Add':'+','Sub':'-'}[op]+f' {vals[1]})'
   lines.append((nid,f'wire [{w-1}:0] {v} = {rhs};'))
  memo[cl]=v;terms[cl]=t;return v,t
 roots=[visit(cl) for cl in graph['root_eclasses']];header='module top('+','.join(f'input [{w-1}:0] {v}' for v in sorted(variables))+','+','.join(f'output [{w-1}:0] y{i}' for i in range(len(roots)))+');'
 text=[header]
 for nid,line in lines:text.append(line);line_nodes[len(text)]=nid
 text += [f'assign y{i} = {v};' for i,(v,t) in enumerate(roots)]+['endmodule']
 return '\n'.join(text)+'\n',line_nodes,[t for v,t in roots],sorted(variables)
def metrics_and_attribution(path,src,line_nodes):
 m=json.loads(path.read_text())['modules']['top'];nodes=m['cells'];known={b:0 for v in m['ports'].values() if v['direction']=='input' for b in v['bits']};known.update({s:0 for s in ['0','1','x','z']});pending=list(nodes.values());allocation={n:0.0 for n in line_nodes.values()};mapped=0;multi=0;cell_map={}
 for ident,cell in nodes.items():
  s=cell.get('attributes',{}).get('src','');matches=re.findall(re.escape(str(src))+r':(\d+)(?:\.\d+)?-(\d+)(?:\.\d+)?',s);owners=set()
  for start,end in matches:owners.update(line_nodes[k] for k in range(int(start),int(end)+1) if k in line_nodes)
  if owners:
   mapped+=1;multi+=len(owners)>1
   for n in owners:allocation[n]+=1/len(owners)
  cell_map[ident]=sorted(owners)
 while pending:
  rest=[]
  for cell in pending:
   bs=[b for p,vs in cell['connections'].items() if cell['port_directions'][p]=='input' for b in vs]
   if any(b not in known for b in bs):rest.append(cell);continue
   dep=1+max((known[b] for b in bs),default=0)
   for p,vs in cell['connections'].items():
    if cell['port_directions'][p]=='output':known.update({b:dep for b in vs})
  assert len(rest)<len(pending),'netlist cycle/undriven';pending=rest
 depth=max(known[b] for v in m['ports'].values() if v['direction']=='output' for b in v['bits'])
 return dict(gates=len(nodes),depth=depth,attribution=allocation,mapped_cells=mapped,multi_source_cells=multi,unmapped_cells=len(nodes)-mapped,coverage=mapped/max(1,len(nodes)),cell_to_enodes=cell_map)
def cone_attribution(path,g,ex):
 m=json.loads(path.read_text())['modules']['top'];cells=m['cells'];net=m['netnames'];ns=g['nodes'];choices=ex['choices'];drivers={}
 for ident,cell in cells.items():
  for p,bs in cell['connections'].items():
   if cell['port_directions'][p]=='output':
    for bit in bs:drivers[bit]=ident
 owners={i:set() for i in cells};selected=[i for i in ex['used_nodes'] if ns[i]['op'] in OPS];missing=[];cones={}
 def signal(i):return net.get('n_'+hashlib.sha256(i.encode()).hexdigest()[:12],{}).get('bits')
 for nid in selected:
  bits=signal(nid)
  if bits is None:missing.append(nid);continue
  boundary=set()
  for child in ns[nid]['children']:
   cn=choices[ns[child]['eclass']]
   if ns[cn]['op'] in OPS:boundary.update(signal(cn) or [])
  todo=list(bits);seen=set();cone=set()
  while todo:
   bit=todo.pop()
   if bit in seen or bit in boundary:continue
   seen.add(bit);cellid=drivers.get(bit)
   if cellid is None:continue
   cone.add(cellid);cell=cells[cellid]
   todo.extend(b for p,bs in cell['connections'].items() if cell['port_directions'][p]=='input' for b in bs)
  cones[nid]=sorted(cone)
  for cellid in cone:owners[cellid].add(nid)
 allocation={nid:0.0 for nid in selected}
 for values in owners.values():
  for nid in values:allocation[nid]+=1/len(values)
 mapped=sum(bool(v) for v in owners.values())
 return dict(attribution=allocation,mapped_cells=mapped,multi_source_cells=sum(len(v)>1 for v in owners.values()),unmapped_cells=len(cells)-mapped,coverage=mapped/max(1,len(cells)),cell_to_enodes={i:sorted(v) for i,v in owners.items()},cones=cones,missing_named_nodes=missing,named_node_coverage=(len(selected)-len(missing))/max(1,len(selected)),attribution_method='named-wire boundary fan-in cones; shared cells fractional; heuristic ownership, not marginal causal area')

def invoke(command,ident,kind):
 ledger=L/'eda_invocations.jsonl';count=sum(1 for l in ledger.read_text().splitlines() if json.loads(l)['kind']=='synthesis') if ledger.exists() else 0
 assert kind!='synthesis' or count<C['maximum_total_synthesis_calls']
 t=time.perf_counter();p=subprocess.run([str(ROOT/'.venv/bin/yowasp-yosys'),'-Q','-T','-p',command],capture_output=True,text=True,timeout=30,env={**os.environ,'XDG_CACHE_HOME':str(ROOT/'.cache')});dt=time.perf_counter()-t
 (L/f'{ident}_{kind}.log.gz').write_bytes(gzip.compress((p.stdout+p.stderr).encode(),mtime=0))
 with ledger.open('a') as f:f.write(json.dumps(dict(id=ident,kind=kind,seconds=dt,returncode=p.returncode))+'\n')
 assert p.returncode==0,(ident,kind,p.stderr)
 if kind=='rtl_sat':assert 'SUCCESS!' in p.stdout
 return dt
def evaluate(g,ex,name,w,ident):
 text,lines,ts,vs=tagged(g,ex,w);refs,_=reference(name,w);v={s:BitVec(s,w) for s in vs};sol=Solver();sol.set(timeout=5000);sol.add(Or(*[zexpr(t,w,v)!=zexpr(r,w,v) for t,r in zip(ts,refs)]));t=time.perf_counter();z=str(sol.check());zt=time.perf_counter()-t;assert z=='unsat'
 src=O/'rtl'/f'{ident}.v';src.parent.mkdir(exist_ok=True);src.write_text(text);dest=Path('results/netlists/attribution_round')/f'{ident}.json';dest.parent.mkdir(parents=True,exist_ok=True)
 st=invoke(f'read_verilog {src}; synth -top top -noabc; write_json {dest}',ident,'synthesis');m=metrics_and_attribution(dest,src,lines);m['cell_source_coverage']=m['coverage'];m.update(cone_attribution(dest,g,ex))
 mit=text.replace('module top(','module dut(')+'module miter('+','.join(f'input [{w-1}:0] {s}' for s in vs)+',output bad);\n'
 for i,r in enumerate(refs):mit+=f'wire [{w-1}:0] y{i}; wire [{w-1}:0] r{i} = {emit(r,w)};\n'
 mit+='dut d('+','.join(f'.{s}({s})' for s in vs)+','+','.join(f'.y{i}(y{i})' for i in range(len(refs)))+');\nassign bad = '+' | '.join(f'(|(y{i} ^ r{i}))' for i in range(len(refs)))+';\nendmodule\n'
 mp=src.with_name(ident+'_miter.v');mp.write_text(mit);sat=invoke(f'read_verilog {mp}; prep -top miter; flatten; sat -verify -prove bad 0',ident,'rtl_sat')
 return dict(**m,id=ident,rtl_sha256=hashlib.sha256(text.encode()).hexdigest(),netlist_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),source_lines=lines,z3=z,rtl_sat=True,z3_seconds=zt,synthesis_seconds=st,sat_seconds=sat,terms=ts)
def solve(g,c,bans):
 cc=dict(c)
 for n in bans:cc[n]=float('inf')
 try:return extract(g,cc)
 except (KeyError,AssertionError):return None

def novel(g,c,seen,w,cap=64):
 # Bounded next-best extraction by excluding selected e-nodes, not PPA lookups.
 counter=0;heap=[];visited={frozenset()};r=solve(g,c,frozenset());attempts=0
 if r:heapq.heappush(heap,(sum(r[1]['tree_root_costs']),counter,frozenset(),r))
 while heap and attempts<cap:
  score,_,bans,r=heapq.heappop(heap);ts,ex=r;attempts+=1;text,*_=tagged(g,ex,w);h=hashlib.sha256(text.encode()).hexdigest()
  if h not in seen:return ts,ex,dict(subproblems=attempts,banned_nodes=sorted(bans),selected_tree_cost=score)
  for n in ex['used_nodes']:
   if g['nodes'][n]['op'] not in OPS:continue
   nb=bans|{n}
   if nb in visited:continue
   visited.add(nb);rr=solve(g,c,nb)
   if rr:
    counter+=1;heapq.heappush(heap,(sum(rr[1]['tree_root_costs']),counter,nb,rr))
 return None

def numerical_update(costs,m,w):
 new=dict(costs);delta={}
 for n,a in m['attribution'].items():
  target=max(.25,a/w);new[n]=target
  if new[n]!=costs[n]:delta[n]=dict(old=costs[n],new=new[n],direction='increase' if new[n]>costs[n] else 'decrease')
 return new,delta

def structural_update(g,c,ex):
 # Same open-loop selector as previous round, independent of measured data.
 from behavior_loop import structural_node
 n=structural_node(g,ex);new=dict(c)
 if n:new[n]+=3
 return new,n

def preflight():
 result=[]
 for item in C['fixtures']:
  g,info=graph_for(item['name']);save(O/'graphs'/f"{item['name']}.json",g);save(O/'graphs'/f"{item['name']}_build.json",info);c=initial_costs(g);seen=set();count=0;effort=[]
  for _ in range(6):
   r=novel(g,c,seen,item['width'])
   if not r:break
   text,*_=tagged(g,r[1],item['width']);seen.add(hashlib.sha256(text.encode()).hexdigest());effort.append(r[2]);count+=1
  assert count==6,'insufficient unique structural alternatives; no EDA sweep authorized by preflight'
  result.append(dict(**item,nodes=len(g['nodes']),graph_sha256=sha(g),unique_fixed_preflight=count,extraction_effort=effort))
 save(O/'preflight.json',result);print(json.dumps(result,indent=2))

def pilot():
 item=C['fixtures'][0];g,info=graph_for(item['name']);c=initial_costs(g);ts,ex=extract(g,c);m=evaluate(g,ex,item['name'],item['width'],'pilot_tagged_mcm_w12');save(O/'pilot_attribution.json',dict(metrics=m,extraction=ex,costs=c));assert m['coverage']>=C['attribution_min_coverage'],'STOP attribution coverage below gate';print(json.dumps({k:v for k,v in m.items() if k not in ['cell_to_enodes','terms']},indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preflight',action='store_true');p.add_argument('--pilot',action='store_true');a=p.parse_args();O.mkdir(exist_ok=True);L.mkdir(exist_ok=True)
 if a.preflight:preflight()
 if a.pilot:pilot()
