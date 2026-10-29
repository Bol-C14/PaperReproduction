import os
import hashlib,json,pathlib,subprocess
R=pathlib.Path(os.environ['REPRO_ROOT']).expanduser().resolve()
base=R/'checkouts/terminal-bench/dataset'
tasks=['log-summary-date-ranges','regex-log','cancel-async-tasks']
allrows=[]
for task in tasks:
    image='localhost/g3-'+task+':calibration'
    code="""import os,pathlib,json,hashlib
roots=['/app','/root','/tmp','/tests','/solution']
files={}
gits=[]
for root in roots:
 for p in pathlib.Path(root).rglob('*'):
  if p.name=='.git': gits.append(str(p))
  if p.is_file() and not p.is_symlink():
   try: files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
   except (OSError,PermissionError): pass
print(json.dumps({'files':files,'git_paths':gits,'mounts':pathlib.Path('/proc/mounts').read_text()}))
"""
    cmd=['podman','run','--rm','--network','none','--memory','2g','--pids-limit','128','--cap-drop','all','--security-opt','no-new-privileges',image,'taskset','-c','0','python','-c',code]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=60,check=True)
    x=json.loads(p.stdout)
    forbidden={hashlib.sha256(f.read_bytes()).hexdigest():str(f.relative_to(base/task)) for folder in ['tests','solution'] for f in (base/task/folder).rglob('*') if f.is_file()}
    x['exact_forbidden_content_matches']={path:forbidden[h] for path,h in x['files'].items() if h in forbidden}
    x['task']=task;x['command']=cmd
    allrows.append(x)
(R/'logs/terminal-bench/isolation-inventory.json').write_text(json.dumps(allrows,indent=2))
print(json.dumps([{'task':x['task'],'scanned_files':len(x['files']),'git_paths':x['git_paths'],'exact_forbidden_content_matches':x['exact_forbidden_content_matches']} for x in allrows],indent=2))
