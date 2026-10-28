"""One comparison mechanism witness; no performance matrix or search retuning."""
import datetime,hashlib,importlib.metadata,json,os,resource,subprocess,sys,time
from pathlib import Path
import z3
from engine import optimize,sx,width,cost
from circuits import emit,symbolic,inputs
from dag_extract import select
from union_domain import comparison_constant,signed_range
ROOT=Path(__file__).resolve().parent
R=Path('/home/shugu/work/paper-reproduction-april-20261028')
OUT=R/'results/rover/comparison_closure_round5_attempt1'
PY=R/'envs/rover/bin/python';YOSYS=R/'envs/rover/bin/yowasp-yosys'
ARMS=('fold_off','fold_on')
def tup(x):return tuple(map(tup,x)) if isinstance(x,list) else x

def witness():
 a=('V','a',8);b=('V','b',1)
 care=('And',('Slt',a,4),('Not',('Slt',a,-3)))
 return ('Mux',1,care,('Slt',a,8),b)
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

def boundary_checks():
 cases=[
  ('ult_true','Ult',((0,3),),4,4,1),
  ('ult_false','Ult',((4,15),),4,4,0),
  ('ult_cross_threshold','Ult',((3,4),),4,4,None),
  ('ult_zero','Ult',((0,15),),4,0,0),
  ('ult_max_boundary','Ult',((0,15),),4,15,None),
  ('signed_union_true','Slt',signed_range(-3,3,4),4,4,1),
  ('signed_union_false','Slt',signed_range(-3,3,4),4,-3,0),
  ('signed_union_cross_zero','Slt',signed_range(-3,3,4),4,0,None),
  ('signed_min','Slt',((8,8),),4,-7,1),
  ('signed_max_equal','Slt',((7,7),),4,7,0),
  ('sge_negative','Sge0',((8,15),),4,None,0),
  ('sge_nonnegative','Sge0',((0,7),),4,None,1),
  ('sge_disjoint_mixed','Sge0',signed_range(-3,3,4),4,None,None),
  ('empty_ult','Ult',(),4,4,None),
  ('empty_slt','Slt',(),4,0,None),
  ('empty_sge','Sge0',(),4,None,None)]
 rows=[]
 for name,op,rs,w,k,expected in cases:
  result=comparison_constant(op,rs,w,k)
  # Independent explicit concrete semantics at the boundary, not circuit samples.
  actual=set()
  for lo,hi in rs:
   for x in range(lo,hi+1):
    signed=x if x<(1<<(w-1)) else x-(1<<w)
    actual.add(int(x<k if op=='Ult' else signed<k if op=='Slt' else signed>=0))
  passed=result==expected and (actual=={result} if result is not None else len(actual)!=1)
  rows.append({'name':name,'op':op,'ranges':rs,'width':w,'constant':k,'expected':expected,'result':result,'concrete_outcomes':sorted(actual),'pass':passed})
 write(OUT/'boundary_checks.json',rows);return rows

def definedness_checks():
 term=witness();p,cmp=term[2:4];original=('Assume',1,cmp,p);folded=('Assume',1,('K',1,1),p)
 empty=('Assume',1,cmp,('And',p,('Not',p)))
 rows=[];d=OUT/'definedness';d.mkdir()
 for name,left,right,expected in [
  ('actual_scoped_fold',original,folded,'unsat'),
  ('reject_naked_constant',original,('K',1,1),'sat'),
  ('empty_is_bottom_not_one',empty,('K',1,1),'sat')]:
  env={n:z3.BitVec(n,b) for n,b in {**inputs(left),**inputs(right)}.items()}
  ld,rd=defined(left,env),defined(right,env);s=z3.Solver();s.set(timeout=15000)
  s.add(z3.Or(ld!=rd,z3.And(ld,rd,symbolic(left,env)!=symbolic(right,env))))
  (d/(name+'.smt2')).write_text(s.to_smt2());t=time.monotonic();status=s.check()
  rows.append({'name':name,'expected':expected,'status':str(status),'pass':str(status)==expected,'wall_s':time.monotonic()-t,'counterexample':str(s.model()) if status==z3.sat else None})
 write(d/'results.json',rows);return rows

def worker(arm):
 start=time.monotonic();term=witness();r=optimize(term,'context_live','union','combine',arm=='fold_on')
 costs={}
 def measure(t):
  for a in t[1:]:
   if isinstance(a,tuple):measure(a)
  costs[sx(t)]=cost(t,costs)
 measure(term);r['shared_delay_targets']=[costs[sx(term)][1]]
 write(OUT/arm/'saturated.json',r)
 r['variants'],r['dag_reports']=select(r['egraph'],r['shared_delay_targets'])
 r['worker_wall_s']=time.monotonic()-start;r['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return r

def record(event):
 with (OUT/'journal.jsonl').open('a') as f:f.write(json.dumps({**event,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})+'\n')

def experiment():
 if (OUT/'journal.jsonl').exists():raise RuntimeError('Refusing existing journal')
 manifest=json.loads((OUT/'manifest.json').read_text())
 for name,digest in manifest['files'].items():
  if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Frozen source changed: '+name)
 t=time.monotonic();record({'event':'begin'});boundaries=boundary_checks();semantics=definedness_checks()
 rows=[];negatives=[];passed=all(x['pass'] for x in boundaries+semantics)
 if passed:
  for arm in ARMS:
   d=OUT/arm;d.mkdir();cmd=[str(PY),str(ROOT/'run.py'),'worker',arm];record({'event':'start','key':arm,'command':cmd});row={'key':arm,'arm':arm}
   try:
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=60)
    (d/'worker.stdout').write_text(p.stdout);(d/'worker.stderr').write_text(p.stderr)
    if p.returncode:raise RuntimeError('optimizer exit '+str(p.returncode))
    r=json.loads(p.stdout);write(d/'optimization.json',r)
    term=witness();expected_union='(union '+sx(('Assume',1,term[3],term[2]))+' '+sx(('Assume',1,('K',1,1),term[2]))+')'
    row.update(worker_wall_s=r['worker_wall_s'],peak_rss_kib=r['peak_rss_kib'],witness_union_present=expected_union in r['dynamic_unions'],variants=[])
    for i,v in enumerate(r['variants']):row['variants'].append({**v,'proof':proof(term,tup(v['term']),d/f'variant{i}','unsat')})
    row['pass']=all(v['proof']['pass'] for v in row['variants']) and row['witness_union_present']==(arm=='fold_on')
   except subprocess.TimeoutExpired as e:
    (d/'worker.stdout').write_bytes(e.stdout or b'');(d/'worker.stderr').write_bytes(e.stderr or b'');row.update(error='optimizer timeout',**{'pass':False})
   except Exception as e:row.update(error=repr(e),**{'pass':False})
   rows.append(row);write(OUT/'partial.json',rows);record({'event':'finish','key':arm,'pass':row['pass'],'error':row.get('error')});print(arm,row['pass'],row.get('error',''),flush=True)
   if not row['pass']:passed=False;break
 if passed:
  original=witness();a=('V','a',8);b=('V','b',1)
  boundary=('Mux',1,('Slt',a,1),('Slt',a,0),b)
  # Whole outputs are checked without imposing a care-domain input assumption.
  for name,lhs,bad in [
   ('global_escape',original,('K',1,1)),
   ('wrong_constant',original,('Mux',1,original[2],('K',1,0),b)),
   ('strict_boundary_wrong_fold',boundary,('Mux',1,boundary[2],('K',1,1),b))]:
   negatives.append({'kind':name,**proof(lhs,bad,OUT/name,'sat')})
  passed=all(x['pass'] for x in negatives)
 summary={'pass':passed,'rows':rows,'boundary_checks':boundaries,'definedness':semantics,'negative_controls':negatives,'wall_s':time.monotonic()-t,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 write(OUT/'summary.json',summary);return 0 if passed else 1

if __name__=='__main__':
 action=sys.argv[1]
 if action=='worker':print(json.dumps(worker(sys.argv[2])));sys.exit()
 if action=='freeze':
  OUT.mkdir(exist_ok=False)
  write(OUT/'manifest.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seed':20261028,'fixture':witness(),'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [*ROOT.glob('*.py'),ROOT/'PROTOCOL.json']},'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'affinity':sorted(os.sched_getaffinity(0)),'thread_limits':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']},'versions':{k:importlib.metadata.version(k) for k in ['egglog','z3-solver','yowasp-yosys']}})
  print('frozen',OUT);sys.exit()
 if action!='run':raise ValueError(action)
 sys.exit(experiment())
