"""Cross-check Python bottom-up costs against native Rust extractor, no EDA."""
import json,time,os
from pathlib import Path
from egglog.bindings import EGraph,CostModel,Extractor,TermDag
from behavior_engine import FIXTURES,HEADER,RULES,build,extract,initial_costs
rows=[]
for name in FIXTURES:
 for pool in ['initial','expanded']:
  for mul in [1,10]:
   g=EGraph();roots=FIXTURES[name];g.parse_and_run_program(HEADER+'\n'.join(f'(let $root{i} {r})' for i,r in enumerate(roots))+'\n'+RULES.read_text())
   for _ in range(3):g.parse_and_run_program('(run constants 1)\n(run algebra 1)'+ ('\n(run proposal 1)' if pool=='expanded' else ''))
   asts=[g.parse_program(f'(extract $root{i})')[0].args[0] for i in range(len(roots))]
   data=json.loads(g.serialize(asts).to_json());costs=initial_costs(data)
   for i,n in data['nodes'].items():
    if n['op']=='Mul':costs[i]=mul
   terms,ext=extract(data,costs)
   enode=lambda op,args:mul if op=='Mul' else 1 if op in ['Add','Sub','Shl'] else 0
   cm=CostModel(lambda sort,n,cs:n+sum(cs),enode,lambda sort,v,cs:sum(cs),lambda sort,v:0)
   extractor=Extractor(None,g,cm);dag=TermDag();rs=[]
   for ast,expected in zip(asts,ext['tree_root_costs']):
    sort,v=g.eval_expr(ast);cost,term=extractor.extract_best(g,dag,v,sort);assert cost==expected,(name,pool,mul,cost,expected);rs.append(dict(cost=cost,term=dag.to_string(term)))
   rows.append(dict(name=name,pool=pool,mul_cost=mul,native_results=rs,cost_match=True))
Path('results/behavior/native_extraction_crosscheck.json').write_text(json.dumps(rows,indent=2));print('PASS 12 native/Python bottom-up fixed-cost comparisons; no synthesis invocations.')
