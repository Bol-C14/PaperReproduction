"""Native egglog rewriting + independent extraction, no candidate oracle.
Bottom-up and greedy DAG worklist algorithms adapted from extraction-gym
903ba0f818b50608fe20ae9e0f03c35cb27bc50a, MIT; license in sources/.
This is a Python adaptation, not execution/performance reproduction of Rust code.
"""
import collections,hashlib,json,time
from pathlib import Path
from egglog.bindings import EGraph
HEADER='(datatype Expr (Num i64) (Var String) (Add Expr Expr) (Sub Expr Expr) (Mul Expr Expr) (Shl Expr i64))\n'
FIXTURES={
'paper_fig4_mul11':['(Mul (Num 11) (Var "x"))'],
'appendix_mcm71931':['(Mul (Num %d) (Var "x"))'%c for c in [7,19,31]],
'fir_style_12_41_21':['(Add (Add (Mul (Num 12) (Var "x0")) (Mul (Num 41) (Var "x1"))) (Mul (Num 21) (Var "x2")))']}
RULES=Path(__file__).resolve().parents[1]/'behavior/table_i_rules.egg'
def build(name,pool,subset,rounds=3,limit=10000):
 t=time.perf_counter();g=EGraph();roots=FIXTURES[name]
 init=HEADER+'\n'.join(f'(let $root{i} {r})' for i,r in enumerate(roots))
 g.parse_and_run_program(init+'\n'+RULES.read_text());exprs=[g.parse_program(f'(extract $root{i})')[0].args[0] for i in range(len(roots))]
 stats=[];rules=['constants']+(['algebra'] if subset=='full' else [])+(['proposal'] if pool=='expanded' else [])
 for iteration in range(rounds):
  program='\n'.join(f'(run {r} 1)' for r in rules)
  report=g.parse_and_run_program(program);d=json.loads(g.serialize(exprs).to_json());stats.append(dict(iteration=iteration+1,nodes=len(d['nodes']),classes=len({v['eclass'] for v in d['nodes'].values()}),report=str(report)))
  if len(d['nodes'])>limit:raise RuntimeError('graph node budget exceeded')
 return d,dict(seconds=time.perf_counter()-t,initial_graph_sha256=hashlib.sha256(init.encode()).hexdigest(),rounds=stats,rulesets=rules)
def initial_costs(d):return {i:1.0 if n['op'] in ['Add','Sub','Mul','Shl'] else 0.0 for i,n in d['nodes'].items()}
def extract(d,costs,algorithm='bottom_up'):
 t=time.perf_counter();nodes=d['nodes'];parents=collections.defaultdict(list)
 for i,n in nodes.items():
  for ch in n['children']:parents[nodes[ch]['eclass']].append(i)
 todo=collections.deque(i for i,n in nodes.items() if not n['children']);queued=set(todo);best={};choice={};costsets={};steps=0
 while todo:
  i=todo.popleft();queued.remove(i);n=nodes[i];cl=n['eclass'];cs=[nodes[ch]['eclass'] for ch in n['children']];steps+=1
  if not all(c in best for c in cs):continue
  if algorithm=='bottom_up':v=costs[i]+sum(best[c] for c in cs)
  else:
   merged={}
   for c in sorted(set(cs)):merged.update(costsets[c])
   if cl in merged:continue
   merged[cl]=costs[i];v=sum(merged.values())
  if v<best.get(cl,float('inf')):
   best[cl]=v;choice[cl]=i
   if algorithm!='bottom_up':costsets[cl]=merged
   for p in parents[cl]:
    if p not in queued:todo.append(p);queued.add(p)
  if steps>1000000:raise RuntimeError('extract iteration limit')
 used=set();active=set()
 def term(cl):
  assert cl not in active,'extraction cycle';active.add(cl);i=choice[cl];used.add(i);n=nodes[i];ts=[term(nodes[ch]['eclass']) for ch in n['children']];active.remove(cl)
  op=n['op']
  if not ts:
   return json.loads(op) if op.startswith('"') else int(op)
  return (op,*ts)
 terms=[term(cl) for cl in d['root_eclasses']]
 return terms,dict(seconds=time.perf_counter()-t,choices=choice,used_nodes=sorted(used),tree_root_costs=[best[c] for c in d['root_eclasses']],dag_cost=sum(costs[i] for i in used),steps=steps)
def emit(t,w):
 op=t[0]
 if op=='Var':return t[1]
 if op=='Num':return f"{w}'d{t[1]%(1<<w)}"
 if op=='Shl':return f'({emit(t[1],w)} << {t[2]})'
 return f'({emit(t[1],w)} '+{'Add':'+','Sub':'-','Mul':'*'}[op]+f' {emit(t[2],w)})'
def zexpr(t,w,vs):
 from z3 import BitVecVal
 op=t[0]
 if op=='Var':return vs[t[1]]
 if op=='Num':return BitVecVal(t[1],w)
 if op=='Shl':return BitVecVal(0,w) if t[2]>=w else zexpr(t[1],w,vs)<<t[2]
 a,b=zexpr(t[1],w,vs),zexpr(t[2],w,vs)
 return {'Add':lambda:a+b,'Sub':lambda:a-b,'Mul':lambda:a*b}[op]()
def reference(name,w):
 x=lambda v:('Var',v);m=lambda c,v:('Mul',('Num',c),x(v))
 if name=='paper_fig4_mul11':return [m(11,'x')],['x']
 if name=='appendix_mcm71931':return [m(c,'x') for c in [7,19,31]],['x']
 return [('Add',('Add',m(12,'x0'),m(41,'x1')),m(21,'x2'))],['x0','x1','x2']
