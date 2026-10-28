import os,sys,json,time,subprocess,hashlib,datetime,resource,itertools
from pathlib import Path
import z3
from engine import optimize,sx,width
from circuits import emit,symbolic,inputs
from dag_extract import select

ROOT=Path(__file__).resolve().parent
R=Path('/home/shugu/work/paper-reproduction-april-20261028')
OUT=R/'results/rover/signed_union_round3'
PY=R/'envs/rover/bin/python'
YOSYS=R/'envs/rover/bin/yowasp-yosys'

def fixtures(w):
 a,b,c=[('V',n,w) for n in ['a','b','c']];k=lambda n:('K',w,n)
 guard=lambda lo,hi:('And',('Slt',a,hi),('Not',('Slt',a,lo)))
 mag=('Abs',w,a)
 return {
 'signed_magnitude_multiply':('Mux',w,guard(-3,4),('Add',w,('Mul',w,mag,('Cut',3,b)),c),c),
 'wrapped_signed_offset':('Mux',w,guard(-3,4),('Mul',w,('Abs',w,('Add',w,a,k(2))),('Cut',3,b)),c),
 'signed_range_mux':('Mux',w,guard(-7,8),('Mux',w,('Slt',a,0),('Neg',w,a),a),c),
 'negative_product':('Mux',w,guard(-4,0),('Mul',w,mag,('Cut',3,b)),c)}

def write(p,v):p.write_text(json.dumps(v,indent=2,default=str)+'\n')
def proof(original,candidate,d,expected):
 d.mkdir();vs={n:z3.BitVec(n,w) for n,w in inputs(original).items()}
 solver=z3.Solver();solver.set(timeout=15000);solver.add(symbolic(original,vs)!=symbolic(candidate,vs))
 (d/'equivalence.smt2').write_text(solver.to_smt2());start=time.monotonic();s=solver.check()
 smt={'status':str(s),'wall_s':time.monotonic()-start,'counterexample':str(solver.model()) if s==z3.sat else None}
 (d/'original.v').write_text(emit(original,'original'));(d/'candidate.v').write_text(emit(candidate,'candidate'))
 ports=inputs(original);decl=', '.join(f'input [{w-1}:0] {n}' for n,w in sorted(ports.items()))
 links=', '.join('.'+n+'('+n+')' for n in sorted(ports));w=width(original)
 (d/'miter.v').write_text(f'module miter({decl}, output fail); wire [{w-1}:0] x,y; original u({links},.out(x)); candidate v({links},.out(y)); assign fail = x != y; endmodule\n')
 (d/'verify.ys').write_text('read_verilog original.v candidate.v miter.v\nhierarchy -top miter\nproc\nflatten\nopt\nsat -verify -prove fail 0 -show-inputs\n')
 command=[str(YOSYS),'-Q','-T','-s','verify.ys'];start=time.monotonic()
 try:
  r=subprocess.run(command,cwd=d,capture_output=True,text=True,timeout=45)
  (d/'yosys.stdout').write_text(r.stdout);(d/'yosys.stderr').write_text(r.stderr)
  status='unsat' if r.returncode==0 and 'SUCCESS' in r.stdout else 'sat' if 'proof did fail' in r.stderr+r.stdout else 'error'
  rtl={'status':status,'exit':r.returncode,'wall_s':time.monotonic()-start,'command':command}
 except subprocess.TimeoutExpired as e:
  (d/'yosys.stdout').write_bytes(e.stdout or b'');(d/'yosys.stderr').write_bytes(e.stderr or b'');rtl={'status':'timeout','wall_s':time.monotonic()-start,'command':command}
 result={'smt':smt,'rtl':rtl,'expected':expected,'pass':smt['status']==expected and rtl['status']==expected};write(d/'result.json',result);return result

def worker(name,w,domain,mode):
 term=fixtures(w)[name];start=time.monotonic();r=optimize(term,mode,domain)
 r['variants'],r['dag_reports']=select(r['egraph'])
 import union_domain
 r['union_analysis_trace']=union_domain.LAST
 r['worker_wall_s']=time.monotonic()-start;r['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return r

if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='worker':
  print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),sys.argv[4],sys.argv[5])));sys.exit()
 if len(sys.argv)>1 and sys.argv[1]=='freeze':
  OUT.mkdir(exist_ok=False)
  manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seed':20261028,'fixtures':{str(w):fixtures(w) for w in [8,16]},'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')}}
  write(OUT/'manifest.json',manifest);print('frozen',OUT);sys.exit()
 if (OUT/'journal.jsonl').exists():raise RuntimeError('Refusing overwrite existing experiment')
 results=[];t=time.monotonic()
 for w in [8,16]:
  for name,term in fixtures(w).items():
   for domain,mode in [('hull','context_live'),('union','agnostic'),('union','context_live')]:
    key=f'{name}_{w}_{domain}_{mode}';d=OUT/key;d.mkdir();cmd=[str(PY),__file__,'worker',name,str(w),domain,mode]
    with (OUT/'journal.jsonl').open('a') as f:f.write(json.dumps({'event':'start','key':key,'command':cmd,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})+'\n')
    row={'key':key,'name':name,'width':w,'domain':domain,'mode':mode}
    try:
     run=subprocess.run(cmd,capture_output=True,text=True,timeout=60,cwd=ROOT)
     (d/'worker.stdout').write_text(run.stdout);(d/'worker.stderr').write_text(run.stderr)
     if run.returncode:raise RuntimeError('worker exit '+str(run.returncode))
     r=json.loads(run.stdout);write(d/'optimization.json',r);row.update(worker_wall_s=r['worker_wall_s'],peak_rss_kib=r['peak_rss_kib'],variants=[])
     for i,v in enumerate(r['variants']):
      # JSON roundtrip restores tuples for emit memoization.
      def tup(x):return tuple(map(tup,x)) if isinstance(x,list) else x
      pr=proof(term,tup(v['term']),d/f'variant{i}', 'unsat');row['variants'].append({**v,'proof':pr})
     row['pass']=all(v['proof']['pass'] for v in row['variants'])
    except Exception as e:row.update(error=repr(e),pass_=False)
    results.append(row);write(OUT/'partial.json',results)
    with (OUT/'journal.jsonl').open('a') as f:f.write(json.dumps({'event':'finish','key':key,'pass':row.get('pass',False),'error':row.get('error')})+'\n')
    print(key,row.get('pass',False),row.get('error',''),flush=True)
 negatives=[]
 for kind in ['wrong_signed_guard','missing_guard','wrong_truncation']:
  w=8;a=('V','a',w);c=('V','c',w);abs_a=('Abs',w,a)
  original=('Mux',w,('Slt',a,4),abs_a,c)
  if kind=='wrong_signed_guard':bad=('Mux',w,('Ult',a,4),abs_a,c)
  elif kind=='missing_guard':bad=abs_a
  else:bad=('Mux',w,('Slt',a,4),('Ext',w,('Cut',2,abs_a)),c)
  negatives.append({'kind':kind,**proof(original,bad,OUT/kind,'sat')})
 write(OUT/'summary.json',{'rows':results,'negative_controls':negatives,'wall_s':time.monotonic()-t,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
