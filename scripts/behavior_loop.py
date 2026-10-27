"""Real online synthesis feedback loop; deterministic non-LLM controller.
Run --pilot before --full. No offline synthesis oracle or cache.
"""
import argparse,copy,gzip,hashlib,itertools,json,os,random,subprocess,time
from pathlib import Path
from z3 import BitVec,Or,Solver,unsat
from behavior_engine import build,extract,initial_costs,reference,emit,zexpr,FIXTURES
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT);CFG=json.loads(Path('configs/behavior.json').read_text())
RUN_DIR=Path(os.environ.get('ASPEN_BEHAVIOR_RUN_ROOT','.'));assert not RUN_DIR.is_absolute() and '..' not in RUN_DIR.parts
OUT=RUN_DIR/'results/behavior';LOG=RUN_DIR/'logs/behavior';OUT.mkdir(parents=True,exist_ok=True);LOG.mkdir(parents=True,exist_ok=True)
def dump(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.parent.name=='graphs':p.with_suffix('.json.gz').write_bytes(gzip.compress(json.dumps(v,indent=2).encode(),mtime=0))
 else:p.write_text(json.dumps(v,indent=2))
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
def rawlog(p,text):p.write_bytes(gzip.compress(text.encode(),mtime=0))
def ledger(v):
 with (LOG/'eda_invocations.jsonl').open('a') as f:f.write(json.dumps(v)+'\n')
def net_metrics(p):
 m=json.loads(p.read_text())['modules']['top'];depth={b:0 for v in m['ports'].values() if v['direction']=='input' for b in v['bits']};depth.update({str(i):0 for i in ['0','1','x','z']});pending=list(m['cells'].values())
 while pending:
  nxt=[]
  for c in pending:
   bs=[b for k,v in c['connections'].items() if c['port_directions'][k]=='input' for b in v]
   if not all(b in depth for b in bs):nxt.append(c);continue
   d=1+max([depth[b] for b in bs] or [0])
   for k,v in c['connections'].items():
    if c['port_directions'][k]=='output':depth.update({b:d for b in v})
  assert len(nxt)<len(pending),'netlist cycle or undriven bit';pending=nxt
 return len(m['cells']),max(depth[b] for v in m['ports'].values() if v['direction']=='output' for b in v['bits'])
def evaluate(terms,name,runid):
 w=CFG['width'];refs,vars=reference(name,w);zs={v:BitVec(v,w) for v in vars};sol=Solver();sol.set(timeout=5000);sol.add(Or(*[zexpr(t,w,zs)!=zexpr(r,w,zs) for t,r in zip(terms,refs)]));z=str(sol.check());assert z=='unsat',(runid,z)
 text=f'module top('+','.join(f'input [{w-1}:0] {v}' for v in vars)+','+','.join(f'output [{w-1}:0] y{i}' for i in range(len(terms)))+');\n'+'\n'.join(f'assign y{i} = {emit(t,w)};' for i,t in enumerate(terms))+'\nendmodule\n'
 src=OUT/'rtl'/f'{runid}.v';src.parent.mkdir(exist_ok=True);src.write_text(text)
 dest=RUN_DIR/'results/netlists/behavior'/f'{runid}.json';dest.parent.mkdir(parents=True,exist_ok=True)
 script=f'read_verilog {src}; synth -top top -noabc; write_json {dest}'
 t=time.perf_counter();p=subprocess.run([str(ROOT/'.venv/bin/yowasp-yosys'),'-Q','-T','-p',script],capture_output=True,text=True,timeout=CFG['synthesis_timeout_s'],env={**os.environ,'XDG_CACHE_HOME':str(ROOT/'.cache')});dt=time.perf_counter()-t
 rawlog(LOG/f'{runid}_synth.log.gz',p.stdout+p.stderr);ledger(dict(id=runid,kind='synthesis',returncode=p.returncode,seconds=dt));assert p.returncode==0 and dest.exists()
 gates,depth=net_metrics(dest)
 m=text.replace('module top(','module dut(')+f'module miter('+','.join(f'input [{w-1}:0] {v}' for v in vars)+',output bad);\n'
 for i,r in enumerate(refs):m+=f'wire [{w-1}:0] y{i}; wire [{w-1}:0] r{i} = {emit(r,w)};\n'
 m+='dut d('+','.join(f'.{v}({v})' for v in vars)+','+','.join(f'.y{i}(y{i})' for i in range(len(refs)))+');\nassign bad = '+' | '.join(f'(|(y{i} ^ r{i}))' for i in range(len(refs)))+';\nendmodule\n'
 mit=src.with_name(runid+'_miter.v');mit.write_text(m)
 t=time.perf_counter();p=subprocess.run([str(ROOT/'.venv/bin/yowasp-yosys'),'-Q','-T','-p',f'read_verilog {mit}; prep -top miter; flatten; sat -verify -prove bad 0'],capture_output=True,text=True,timeout=CFG['synthesis_timeout_s'],env={**os.environ,'XDG_CACHE_HOME':str(ROOT/'.cache')});satdt=time.perf_counter()-t
 rawlog(LOG/f'{runid}_sat.log.gz',p.stdout+p.stderr);ledger(dict(id=runid,kind='rtl_sat',returncode=p.returncode,seconds=satdt));ok=p.returncode==0 and 'SUCCESS!' in p.stdout;assert ok,runid
 return dict(gates=gates,depth=depth,z3=z,rtl_sat=ok,synthesis_seconds=dt,sat_seconds=satdt,rtl_sha256=hashlib.sha256(text.encode()).hexdigest(),netlist_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),rtl=str(src))
def select_rules(mode,history,baseline,seed):
 if mode=='static' or not history:return 'full'
 # Deterministic history-conditioned heuristic, no learned/LLM policy.
 if min(v['gates'] for v in history)<baseline:return 'full'
 return 'constants_only'
def update_costs(graph,costs,ex,metric,best,previous_snapshot=None):
 before=copy.deepcopy(costs);costs=copy.deepcopy(costs);rollback=previous_snapshot is not None and metric>best
 if rollback:costs=copy.deepcopy(previous_snapshot)
 ns=graph['nodes'];mul=[i for i in ex['used_nodes'] if ns[i]['op']=='Mul'];others=[i for i in ex['used_nodes'] if ns[i]['op']=='Add']
 # Local selected e-node update; prioritization reads structure only.
 def coefficient(i):
  values=[]
  for ch in ns[i]['children']:
   n=ns[ch]
   if n['op']=='Num':
    for p in n['children']:
     try:values.append(int(ns[p]['op']))
     except ValueError:pass
  return max(values or [0])
 eligible=mul or others;chosen=max(eligible,key=lambda i:(coefficient(i),i)) if eligible else None
 delta=CFG['cost_delta']*(2 if metric>best else 1)
 if chosen:costs[chosen]+=delta
 return costs,dict(before=digest(before),after=digest(costs),selected_node=chosen,delta=delta if chosen else 0,rollback=rollback,metric=metric,best_before=best,snapshot_before_update=before)
def session(name,pool,selection,costmode,seed,tag):
 runid=f'{tag}_{name}_{pool}_{selection}_{costmode}_s{seed}';tall=time.perf_counter();refs,_=reference(name,CFG['width']);base=evaluate(refs,name,runid+'_reference');records=[];history=[]
 for outer in range(CFG['outer_iterations']):
  st=time.perf_counter();subset=select_rules(selection,history,base['gates'],seed);selection_seconds=time.perf_counter()-st
  graph,info=build(name,pool,subset,CFG['graph_rounds'],CFG['graph_node_limit']);dump(OUT/'graphs'/f'{runid}_o{outer}.json',graph);dump(OUT/'graphs'/f'{runid}_o{outer}_build.json',info);costs=initial_costs(graph);best=base['gates'];snapshot=None
  for inner in range(CFG['inner_iterations']):
   terms,ex=extract(graph,costs,CFG['chosen_extractor']);shadow,shadowex=extract(graph,costs,'greedy_dag')
   rid=f'{runid}_o{outer}_i{inner}';metric=evaluate(terms,name,rid);st=time.perf_counter();action=None
   if costmode=='feedback':
    costs,action=update_costs(graph,costs,ex,metric['gates'],best,snapshot);snapshot=action['snapshot_before_update']
   control_seconds=time.perf_counter()-st
   r=dict(id=rid,outer=outer,inner=inner,subset=subset,terms=terms,rendered=[emit(v,CFG['width']) for v in terms],extraction=ex,greedy_shadow=dict(rendered=[emit(v,CFG['width']) for v in shadow],**shadowex),metrics=metric,action=action,rule_selection_seconds=selection_seconds if inner==0 else 0,graph_seconds=info['seconds'] if inner==0 else 0,controller_seconds=control_seconds,graph_nodes=len(graph['nodes']),costs_after=costs)
   records.append(r);history.append(metric);best=min(best,metric['gates']);dump(OUT/'runs'/f'{rid}.json',r)
 assert len(records)+1==CFG['true_synthesis_budget_per_session']
 s=dict(id=runid,name=name,pool=pool,selection=selection,cost=costmode,seed=seed,baseline=base,records=[r['id'] for r in records],budget=7,true_synthesis_calls=7,rtl_sat_calls=7,best_gates=min([base['gates']]+[r['metrics']['gates'] for r in records]),best_depth=min([base['depth']]+[r['metrics']['depth'] for r in records]),unique_rtl=len({base['rtl_sha256']}|{r['metrics']['rtl_sha256'] for r in records}),seconds=time.perf_counter()-tall,initial_graph_hashes=[json.loads(gzip.decompress((OUT/'graphs'/f'{runid}_o{o}_build.json.gz').read_bytes()))['initial_graph_sha256'] for o in range(2)])
 dump(OUT/'sessions'/f'{runid}.json',s);print(json.dumps({k:v for k,v in s.items() if k not in ['records','initial_graph_hashes','baseline']}),flush=True);return s

def figure4():
 graph,info=build('paper_fig4_mul11','initial','full');rows=[]
 for model in ['uniform','global_mul10','local_mul11_4']:
  costs=initial_costs(graph)
  for i,n in graph['nodes'].items():
   if n['op']=='Mul':
    if model=='global_mul10':costs[i]=10
    if model=='local_mul11_4' and any(graph['nodes'][j]['op']=='Num' and any(graph['nodes'][k]['op']=='11' for k in graph['nodes'][j]['children']) for j in n['children']):costs[i]=4
  for alg in ['bottom_up','greedy_dag']:
   terms,ex=extract(graph,costs,alg);m=evaluate(terms,'paper_fig4_mul11','figure4_'+model) if alg=='bottom_up' else None;rows.append(dict(model=model,algorithm=alg,rendered=[emit(t,8) for t in terms],metrics=m,**ex))
 dump(OUT/'figure4.json',dict(graph=graph,build=info,rows=rows))
 # Controlled intervention on response dependency; no additional EDA.
 costs=initial_costs(graph);terms,ex=extract(graph,costs);a,ai=update_costs(graph,costs,ex,100,100);b,bi=update_costs(graph,costs,ex,101,100)
 assert digest(a)!=digest(b)
 assert select_rules('feedback',[{'gates':90}],100,0)!=select_rules('feedback',[{'gates':110}],100,0)
 dump(OUT/'feedback_dependency.json',dict(cost_response_sensitivity=True,rule_response_sensitivity=True,kind='controlled response intervention; not a performance measurement',cost_delta_good=ai['delta'],cost_delta_bad=bi['delta']))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');p.add_argument('--full',action='store_true');a=p.parse_args()
 if a.pilot:
  assert not list((OUT/'sessions').glob('pilot*.json')), 'Choose a new ASPEN_BEHAVIOR_RUN_ROOT; recorded pilot exists'
  session('paper_fig4_mul11','expanded','feedback','feedback',0,'pilot')
 if a.full:
  assert not list((OUT/'sessions').glob('factorial*.json')), 'Choose a new ASPEN_BEHAVIOR_RUN_ROOT; recorded factorial exists'
  from validate_proposals import validate
  dump(OUT/'proposal_validation.json',validate())
  for name,seed,pool,selection,cost in itertools.product(CFG['benchmarks'],CFG['seeds'],['initial','expanded'],['static','feedback'],['static','feedback']):session(name,pool,selection,cost,seed,'factorial')
  figure4()
