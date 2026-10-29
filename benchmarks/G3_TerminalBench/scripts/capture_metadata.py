import os
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

R=Path(os.environ['REPRO_ROOT']).expanduser().resolve()
A=R/'assets/terminal-bench'; C=R/'checkouts/terminal-bench'; L=R/'logs/terminal-bench'
def command(*args):
    p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
    return {'argv':list(args),'exit_code':p.returncode,'output':p.stdout}
def files(path):
    return {str(p.relative_to(path)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(path.rglob('*')) if p.is_file()}
x={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':files(A/'sources'),'selection':json.loads((A/'selection.json').read_text()),'ports':files(A/'ports'),'builds':files(A/'build'),'repositories':{},'tools':{},'images':{}}
for name in ['dataset','harbor','protocol-4']:
    p=C/name
    x['repositories'][name]={'commit':command('git','-C',str(p),'rev-parse','HEAD'),'status':command('git','-C',str(p),'status','--short'),'license_files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.glob('*') if f.is_file() and 'license' in f.name.lower()}}
for c in [('podman','--version'),('crun','--version'),('uv','--version'),('git','--version'),(str(R/'envs/terminal-bench/venv/bin/python'),'--version'),(str(R/'envs/terminal-bench/venv/bin/podman-compose'),'--version')]: x['tools'][c[0]]=command(*c)
for t in x['selection']['tasks']:
    image='localhost/g3-'+t+':calibration'
    inspect=command('podman','image','inspect',image)
    (L/('final-image-'+t+'.json')).write_text(inspect['output'])
    x['images'][t]=json.loads(inspect['output'])[0]
    packages=command('podman','run','--rm','--network','none','--memory','2g','--pids-limit','128','--cap-drop','all','--security-opt','no-new-privileges',image,'taskset','-c','0','bash','-c','python --version; python -m pip freeze; dpkg-query -W -f=\'${Package} ${Version}\\n\'')
    (L/('final-packages-'+t+'.txt')).write_text(json.dumps(packages,indent=2))
(A/'metadata.json').write_text(json.dumps(x,indent=2))
print(json.dumps({'repos':{k:v['commit']['output'].strip() for k,v in x['repositories'].items()},'images':{k:v['Id'] for k,v in x['images'].items()},'source_count':len(x['sources'])},indent=2))
