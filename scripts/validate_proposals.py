"""Trusted schema-specific checks for deterministic Appendix-A replay.
Finite widths/count instances; not a universal theorem for all RTL types.
"""
import json,time,os
from pathlib import Path
from z3 import *
def validate():
 rows=[]
 for w in [8,16,32]:
  x,a,b=BitVecs('x a b',w);bv=lambda n:BitVecVal(n,w)
  sh=lambda v,k:bv(0) if k>=w else v<<k
  cs=[('double_add',x+x,sh(x,1)),('mul7',7*x,sh(x,3)-x),('mul31',31*x,sh(x,5)-x),('mul19',19*x,sh(x,4)+sh(x,1)+x),('mul12',12*x,sh(x,3)+sh(x,2)),('mul41',41*x,sh(x,5)+sh(x,3)+x),('mul21',21*x,sh(x,4)+sh(x,2)+x)]
  cs += [(f'factor_shift_k{k}',sh(a,k)+sh(b,k),sh(a+b,k)) for k in range(10)]
  for name,l,r in cs:
   s=Solver();s.set(timeout=5000);s.add(l!=r);t=time.perf_counter();result=str(s.check());assert result=='unsat',(name,w,result);rows.append(dict(rule=name,width=w,result=result,seconds=time.perf_counter()-t))
 return rows
if __name__=='__main__':
 p=Path(__file__).resolve().parents[1]/Path(os.environ.get('ASPEN_BEHAVIOR_RUN_ROOT','.'))/'results/behavior/proposal_validation.json';r=validate();p.write_text(json.dumps(r,indent=2));print(f'{len(r)} finite obligations UNSAT; deterministic source rules accepted under recorded uniform-width semantics.')
