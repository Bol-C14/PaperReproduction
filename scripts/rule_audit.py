"""Independent trusted formulas; never execute LLM-generated proof scripts."""
import json,time
from pathlib import Path
from z3 import *
rows=[]
for w in [1,2,4,8,16,32]:
 x,a,b,c,k,s=BitVecs('x a b c k s',w)
 bv=lambda n:BitVecVal(n,w)
 sh=lambda v,n: bv(0) if n>=w else v<<n
 cases=[('double_add',x+x,sh(x,1),True),('mul12',12*x,(sh(x,3))+(sh(x,2)),True),('mul41',41*x,(sh(x,5))+(sh(x,3))+x,True),('mul21',21*x,(sh(x,4))+(sh(x,2))+x,True),('mul7_via3',7*x,(sh((3*x),1))+x,True),('mul21_via7',21*x,(sh((7*x),1))+7*x,True),('mul93',93*x,(sh(x,6))+(sh(x,4))+(sh(x,3))+(sh(x,2))+x,True),('factor_shift',(a<<c)+(b<<c),(a+b)<<c,True),('merge_shifts_wrapped_count',(x<<c)<<k,x<<(c+k),True),('merge_shifts_widened_count',(x<<c)<<k,Extract(w-1,0,ZeroExt(w,x)<<(ZeroExt(w,c)+ZeroExt(w,k))),True),('and_or_mux_vector',(a&~s)|(b&s),If(s!=0,b,a),True),('and_or_mux_bool',(a&~s)|(b&s),If(s!=0,b,a),Or(s==0,s==1)),('and_or_mux_fullmask',(a&~s)|(b&s),If(s!=0,b,a),Or(s==0,s==bv((1<<w)-1))),('arithmetic_mux_vector',a*b+c*~b,If(b!=0,a,c),True),('arithmetic_mux_boolean_complement',a*b+c*(1-b),If(b!=0,a,c),Or(b==0,b==1))]
 for name,lhs,rhs,guard in cases:
  sol=Solver();sol.set(timeout=5000);sol.add(guard,lhs!=rhs);t=time.perf_counter();out=sol.check();r={'rule':name,'width':w,'result':str(out),'seconds':time.perf_counter()-t}
  if out==sat:
   m=sol.model();r['counterexample']={str(v):m.eval(v,model_completion=True).as_long() for v in [x,a,b,c,k,s]};r['lhs']=m.eval(lhs).as_long();r['rhs']=m.eval(rhs).as_long()
  expected_sat = (name=='merge_shifts_wrapped_count' or (w>1 and name in ['and_or_mux_vector','and_or_mux_bool','arithmetic_mux_vector']))
  assert (out==sat if expected_sat else out==unsat), (name,w,out)
  rows.append(r)
Path('results/rule_audit.json').write_text(json.dumps(rows,indent=2))
print(json.dumps({'checks':len(rows),'sat':sum(r['result']=='sat' for r in rows),'unsat':sum(r['result']=='unsat' for r in rows),'unknown':sum(r['result']=='unknown' for r in rows)}))
