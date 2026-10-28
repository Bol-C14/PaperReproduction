"""Bounded paired nested-context experiment; originals and every attempt retained."""
import os,sys,json,time,subprocess,hashlib,datetime,resource,importlib.metadata
from pathlib import Path
import z3
from engine import optimize,sx,width,conjunction,cost
from circuits import emit,symbolic,inputs
from dag_extract import select
ROOT=Path(__file__).resolve().parent
R=Path('/home/shugu/work/paper-reproduction-april-20261028')
OUT=R/'results/rover/nested_combine_round4_attempt2'
PY=R/'envs/rover/bin/python'
YOSYS=R/'envs/rover/bin/yowasp-yosys'
ARMS=('legacy','propagate','combine')
def tup(x):return tuple(map(tup,x)) if isinstance(x,list) else x

def fixtures(w):
 a,b,c=[('V',n,w) for n in ('a','b','c')]; k=lambda n:('K',w,n)
 mul=lambda x,y:('Mul',w,x,y)
 signed_guard=('And',('Slt',a,8),('Not',('Slt',a,-7)))
 return {
  'nested_signed_product':('Mux',w,signed_guard,('Mux',w,('Slt',a,0),mul(('Neg',w,a),('Cut',3,b)),mul(a,('Cut',3,b))),c),
  'nested_independent_bounds':('Mux',w,('Ult',a,8),('Mux',w,('Ult',b,4),('Add',w,mul(a,b),k(1)),c),c),
  'nested_false_branch':('Mux',w,('Ult',a,16),('Mux',w,('Ult',a,4),c,mul(a,('Cut',3,b))),c)}
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

def defined(t,env):
 op=t[0]
 if op in ('V','K'):return z3.BoolVal(True)
 if op=='Assume':return z3.And(defined(t[2],env),defined(t[3],env),symbolic(t[3],env)!=0)
 if op=='Mux':return z3.And(defined(t[2],env),z3.If(symbolic(t[2],env)!=0,defined(t[3],env),defined(t[4],env)))
 return z3.And(*[defined(a,env) for a in t[1:] if isinstance(a,tuple)])

def semantic_checks():
 w=8;a=('V','a',w);b=('V','b',w);p=('V','p',1);q=('V','q',1)
 assume=lambda x,g:('Assume',w,x,g)
 mux=lambda g,x,y:('Mux',w,g,x,y)
 nested=assume(assume(a,p),q)
 both=conjunction(p,q)
 contradictory=assume(a,conjunction(p,('Not',p)))
 cases=[
  ('combine',nested,assume(a,both),'unsat'),
  ('combine_duplicate',assume(nested,p),assume(a,conjunction(p,q,p)),'unsat'),
  ('mux_propagate',assume(mux(q,a,b),p),mux(q,assume(a,p),assume(b,p)),'unsat'),
  ('create',mux(p,a,b),mux(p,assume(a,p),assume(b,('Not',p))),'unsat'),
  ('strict_add_propagate',assume(('Add',w,a,b),p),('Add',w,assume(a,p),assume(b,p)),'unsat'),
  ('wrong_combine_or',nested,assume(a,('Not',('And',('Not',p),('Not',q)))),'sat'),
  ('drop_outer_assumption',nested,assume(a,p),'sat'),
  ('bottom_as_zero',contradictory,('K',w,0),'sat')]
 d=OUT/'definedness';d.mkdir();rows=[]
 for name,lhs,rhs,expected in cases:
  env={n:z3.BitVec(n,bits) for n,bits in {**inputs(lhs),**inputs(rhs)}.items()}
  ld,rd=defined(lhs,env),defined(rhs,env)
  s=z3.Solver();s.set(timeout=15000);s.add(z3.Or(ld!=rd,z3.And(ld,rd,symbolic(lhs,env)!=symbolic(rhs,env))))
  (d/(name+'.smt2')).write_text(s.to_smt2());t=time.monotonic();status=s.check()
  rows.append({'name':name,'expected':expected,'status':str(status),'pass':str(status)==expected,'counterexample':str(s.model()) if status==z3.sat else None,'wall_s':time.monotonic()-t})
 write(d/'results.json',rows);return rows

def worker(name,w,arm):
 start=time.monotonic();term=fixtures(w)[name];r=optimize(term,'context_live','union',arm)
 costs={}
 def measure(t):
  for a in t[1:]:
   if isinstance(a,tuple):measure(a)
  costs[sx(t)]=cost(t,costs)
 measure(term);original_delay=costs[sx(term)][1]
 r['shared_delay_targets']=[original_delay,2*original_delay]
 write(OUT/f'{name}_{w}_{arm}'/'saturated.json',r)
 r['variants'],r['dag_reports']=select(r['egraph'],r['shared_delay_targets'])
 import union_domain
 r['union_analysis_trace']=union_domain.LAST
 r['worker_wall_s']=time.monotonic()-start;r['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return r

def record(row):
 with (OUT/'journal.jsonl').open('a') as f:f.write(json.dumps({**row,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})+'\n')

def experiment(stage):
 if (OUT/'journal.jsonl').exists():raise RuntimeError('Refusing existing attempt journal')
 manifest=json.loads((OUT/'manifest.json').read_text())
 for name,digest in manifest['files'].items():
  if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Frozen source changed: '+name)
 results=[];start=time.monotonic();semantics=semantic_checks()
 pairs=[(8,'nested_signed_product')] if stage=='pilot' else [(w,n) for w in (8,16) for n in fixtures(w)]
 stop=False
 for w,name in pairs:
  for arm in ARMS:
   key=f'{name}_{w}_{arm}';d=OUT/key;d.mkdir();cmd=[str(PY),str(ROOT/'run.py'),'worker',name,str(w),arm]
   record({'event':'start','key':key,'command':cmd});row={'key':key,'name':name,'width':w,'arm':arm}
   try:
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=60)
    (d/'worker.stdout').write_text(p.stdout);(d/'worker.stderr').write_text(p.stderr)
    if p.returncode:raise RuntimeError('worker exit '+str(p.returncode))
    r=json.loads(p.stdout);write(d/'optimization.json',r)
    row.update(worker_wall_s=r['worker_wall_s'],peak_rss_kib=r['peak_rss_kib'],variants=[])
    for i,v in enumerate(r['variants']):
     pr=proof(fixtures(w)[name],tup(v['term']),d/f'variant{i}','unsat')
     row['variants'].append({**v,'proof':pr})
    row['pass']=all(v['proof']['pass'] for v in row['variants'])
   except subprocess.TimeoutExpired as e:
    (d/'worker.stdout').write_bytes(e.stdout or b'');(d/'worker.stderr').write_bytes(e.stderr or b'');row.update(error='worker timeout',**{'pass':False})
   except Exception as e:row.update(error=repr(e),**{'pass':False})
   results.append(row);write(OUT/'partial.json',results);record({'event':'finish','key':key,'pass':row['pass'],'error':row.get('error')})
   print(key,row['pass'],row.get('error',''),flush=True)
   if not row['pass']:stop=True;break
  if stop:break
 negatives=[]
 if not stop:
  w=8;a=('V','a',w);b=('V','b',w);c=('V','c',w)
  term=fixtures(w)['nested_independent_bounds'];inner=term[3]
  # All mismatches must be visible in the complete module without external assumptions.
  for kind,bad in [
    ('drop_outer_guard',inner),
    ('wrong_inner_polarity',('Mux',w,term[2],('Mux',w,('Not',inner[2]),inner[3],inner[4]),c)),
    ('unconditional_narrowing',('Add',w,('Ext',w,('Mul',5,('Cut',3,a),('Cut',2,b))),('K',w,1)))]:
   negatives.append({'kind':kind,**proof(term,bad,OUT/kind,'sat')})
 summary={'stage':stage,'rows':results,'definedness':semantics,'negative_controls':negatives,'wall_s':time.monotonic()-start,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 summary['pass']=not stop and all(x['pass'] for x in semantics+negatives)
 write(OUT/'summary.json',summary)
 return 0 if summary['pass'] else 1

if __name__=='__main__':
 action=sys.argv[1]
 if action=='worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),sys.argv[4])));sys.exit()
 if action=='freeze':
  OUT.mkdir(exist_ok=False)
  manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seed':20261028,'affinity':sorted(os.sched_getaffinity(0)),'thread_limits':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']},'fixtures':{str(w):fixtures(w) for w in (8,16)},'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [*ROOT.glob('*.py'),ROOT/'PROTOCOL.json']},'versions':{k:importlib.metadata.version(k) for k in ['egglog','z3-solver','yowasp-yosys']},'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
  write(OUT/'manifest.json',manifest);print('frozen',OUT);sys.exit()
 if action not in ('pilot','matrix'):raise ValueError(action)
 sys.exit(experiment(action))
