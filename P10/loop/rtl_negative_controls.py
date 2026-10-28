"""Independent RTL checker sensitivity controls; expected SAT failures retained."""
import json,pathlib,time
import z3
from circuits import emit,inputs,symbolic
from engine import width
from run_loop import run,ROOT

cases=[]
a,y,b=('V','a',8),('V','y',4),('V','b',8)
c=('Ult',y,3)
cases.append(('invalid_guard',('Mux',8,c,('Shr',8,a,y),b),('Mux',8,c,('Shr',8,a,('Cut',1,y)),b)))
x=('V','x',4)
cases.append(('signedness',('Abs',4,x),x))
a,b=('V','a',4),('V','b',4)
cases.append(('truncation',('Add',8,a,b),('Ext',8,('Add',4,a,b))))
out=ROOT/'runs'/'negative_rtl1';out.mkdir(exist_ok=False);rows=[]
for name,original,bad in cases:
    folder=out/name;folder.mkdir();env={n:z3.BitVec(n,w) for n,w in inputs(original).items()}
    s=z3.SolverFor('QF_BV');s.set(timeout=10000,random_seed=0);s.add(symbolic(original,env)!=symbolic(bad,env));status=s.check()
    (folder/'design.v').write_text(emit(original,'original')+emit(bad,'candidate'))
    ports=', '.join(f'input [{w-1}:0] {n}' for n,w in sorted(inputs(original).items()))
    def inst(t,m,out):return f'{m} u_{m}('+', '.join(f'.{n}({n})' for n in sorted(inputs(t)))+f', .out({out}));'
    miter=f'module miter({ports},output mismatch);wire [{width(original)-1}:0] refout,testout;'+inst(original,'original','refout')+inst(bad,'candidate','testout')+'assign mismatch=|(refout^testout);endmodule\n'
    (folder/'miter.v').write_text(miter)
    (folder/'verify.ys').write_text('read_verilog design.v miter.v\nprep -top miter -flatten\nsat -verify -prove mismatch 0 -show-inputs\n')
    r=run([str(ROOT/'.venv/bin/yowasp-yosys'),'-s','verify.ys'],folder,folder/'verify.log',120)
    text=(folder/'verify.log').read_text()
    row={'control':name,'z3':str(status),'witness':str(s.model()) if status==z3.sat else None,'rtl':r,
         'passed':status==z3.sat and r.get('returncode')==1 and 'proof did fail' in text}
    rows.append(row);print(row)
(out/'RESULTS.json').write_text(json.dumps(rows,indent=2))
if not all(r['passed'] for r in rows):raise SystemExit(1)
