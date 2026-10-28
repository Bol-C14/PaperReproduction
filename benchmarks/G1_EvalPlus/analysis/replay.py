"""APRIL-only bounded controller; cached code is never executed on the host."""
import concurrent.futures,gzip,hashlib,json,os,pathlib,subprocess,zipfile
ROOT=pathlib.Path(os.environ['EVALPLUS_REPRO_ROOT']).resolve()
A=ROOT/'assets/evalplus'; R=ROOT/'results/evalplus'; U=ROOT/'checkouts/evalplus/upstream'; V=ROOT/'envs/evalplus'; S=ROOT/'checkouts/evalplus/analysis'
IDS=[0,1,2,3,6,9,28,32,35,53,58,75,99,114,124,129,140,148,160,163]
selection={'task_ids':['HumanEval/'+str(i) for i in IDS],'reason':'Purposive frozen sample covering documented oracle/contract updates and paper examples plus endpoint 163; selected before reading cache outcomes. Not representative random sampling.','development_models':['chatgpt','codegen-2b'],'held_out_models':['gpt-4'],'programs_per_model_per_task':1,'sample':'0.py','temperature':0.0,'cost_cap_usd':0,'cpu_threads':4,'download_cap_bytes':2000000000,'setup_cap_hours':2}
R.mkdir(parents=True,exist_ok=True);(R/'selection.json').write_text(json.dumps(selection,indent=2))
cpus=sorted(os.sched_getaffinity(0))[:4]
base=['/usr/bin/taskset','-c',','.join(map(str,cpus)),'/usr/bin/timeout','180','/usr/bin/bwrap','--unshare-all','--die-with-parent','--new-session','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--ro-bind',str(V),'/venv','--ro-bind',str(U),'/upstream','--ro-bind',str(S),'/runner','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--tmpfs','/dev/shm','--chdir','/tmp','--clearenv','--setenv','PATH','/usr/bin','--setenv','HOME','/tmp','--setenv','OPENBLAS_NUM_THREADS','1','--setenv','OMP_NUM_THREADS','1','--setenv','EVALPLUS_MAX_MEMORY_BYTES','1073741824','/usr/bin/prlimit','--cpu=120:120','--as=2147483648','--fsize=16777216','--nofile=128','/venv/bin/python']
# Synthetic negative-access control, including actual mounts; no secrets inspected.
probe="""import os,pathlib,socket,numpy,psutil
assert not pathlib.Path('/home').exists()
assert not pathlib.Path('/proc/1/root/home').exists()
assert not pathlib.Path('/root/.ssh').exists()
assert not pathlib.Path('/assets').exists()
assert not pathlib.Path('/results').exists()
assert not any(k for k in os.environ if any(s in k.lower() for s in ['key','token','secret','proxy']))
s=socket.socket();s.settimeout(.2);assert s.connect_ex(('192.0.2.1',9))!=0
assert len(pathlib.Path('/proc/net/route').read_text().splitlines())==1
try: pathlib.Path('/upstream/UNAUTHORIZED').write_text('synthetic');raise AssertionError('writable')
except OSError: pass
print('all synthetic access assertions satisfied')
"""
p=subprocess.run(base+['-c',probe],capture_output=True,text=True,env={'PATH':'/usr/bin'},timeout=190)
(R/'isolation.json').write_text(json.dumps({'command':base+['-c',probe],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2))
assert p.returncode==0,p.stderr
if os.environ.get('ISOLATION_ONLY')=='1': raise SystemExit(0)
D={x['task_id']:x for x in map(json.loads,gzip.open(A/'HumanEvalPlus-v0.1.10.jsonl.gz','rt'))}
phase=os.environ.get('REPLAY_PHASE','development')
models=['chatgpt','codegen-2b'] if phase=='development' else (['gpt-4'] if phase=='held_out' else ['chatgpt','codegen-2b','gpt-4'])
archives={m:zipfile.ZipFile(A/(m+'_temp_0.0.zip')) for m in models}
if phase!='development': assert (R/'frozen-reduction.json').is_file(), 'Freeze development reduction first'
if phase=='combined':
 reduction=json.loads((R/'frozen-reduction.json').read_text())['tasks']
 IDS=[i for i in IDS if i!=32]
 for i in IDS:
  tid='HumanEval/'+str(i);t=D[tid].copy();t['plus_input']=[D[tid]['plus_input'][j] for j in reduction[tid]['selected_plus_indices']['combined']];D[tid]=t
R=R/phase;R.mkdir(exist_ok=True)
pins=[]
def run(i):
 tid='HumanEval/'+str(i); samples={}
 for m,z in archives.items():
  paths=[n for n in z.namelist() if n.endswith('/HumanEval_'+str(i)+'/0.py')]
  if len(paths)!=1: return {'task_id':tid,'status':'cache_missing','model':m,'matches':paths}
  data=z.read(paths[0]);samples[m]=data.decode();pins.append({'task_id':tid,'model':m,'archive_member':paths[0],'sha256':hashlib.sha256(data).hexdigest()})
 job={'task':D[tid],'samples':samples,'phase':phase,'minimal':phase=='combined'}
 try:
  p=subprocess.run(base+['/runner/worker.py'],input=json.dumps(job),capture_output=True,text=True,env={'PATH':'/usr/bin'},timeout=190)
  (R/(str(i)+'.raw.json')).write_text(json.dumps({'command':base+['/runner/worker.py'],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2))
  result=json.loads(p.stdout) if p.returncode==0 else {'task_id':tid,'status':'sandbox_failure','exit':p.returncode}
 except subprocess.TimeoutExpired: result={'task_id':tid,'status':'outer_timeout','seconds':190}
 (R/(str(i)+'.json')).write_text(json.dumps(result));print(tid,result['status'],flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: results=list(ex.map(run,IDS))
(R/'sample-pins.json').write_text(json.dumps(sorted(pins,key=lambda x:(x['task_id'],x['model'])),indent=2))
if phase=='combined': results.append({'task_id':'HumanEval/32','status':'invalid_evaluator','reason':'root oracle skips bookkeeping; preserved original results, excluded reduced rerun'})
(R/'all-results.json').write_text(json.dumps(results))
metadata={'assets':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in A.iterdir() if p.is_file()},'harness_head':subprocess.check_output(['git','-C',str(U),'rev-parse','HEAD'],text=True).strip(),'python':subprocess.check_output([str(V/'bin/python'),'--version'],text=True).strip(),'pip_freeze':subprocess.check_output([str(V/'bin/pip'),'freeze'],text=True).splitlines(),'bwrap':subprocess.check_output(['bwrap','--version'],text=True).strip()}
(R/'pins.json').write_text(json.dumps(metadata,indent=2))
