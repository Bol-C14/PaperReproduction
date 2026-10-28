"""Bounded Podman port of pinned upstream runtime_files, with private inputs.

This does not launch Harbor or agents. It reuses native per-task simulation
scripts and immutable images, and saves exit codes plus full raw simulation logs.
"""
import argparse, ast, dataclasses, hashlib, json, os, pathlib, subprocess, time, types

p=argparse.ArgumentParser()
p.add_argument('--upstream',type=pathlib.Path,required=True)
p.add_argument('--datasets',type=pathlib.Path,required=True)
p.add_argument('--selection',type=pathlib.Path,required=True)
p.add_argument('--images',type=pathlib.Path,required=True)
p.add_argument('--root',type=pathlib.Path,required=True)
a=p.parse_args();a.root.mkdir(parents=True,exist_ok=True)
store=a.root/'containers';runroot=a.root/'runroot'
pod=['podman','--root',str(store),'--runroot',str(runroot),'--storage-driver','overlay']
cpus=','.join(map(str,sorted(os.sched_getaffinity(0))[:4]))
records={f"{r['org']}/{r['repo']}:pr-{r['number']}":r for f in a.datasets.glob('*.jsonl') if not f.name.startswith('._') for r in map(json.loads,f.read_text().splitlines())}
images={r['id']:r for r in json.loads(a.images.read_text())}
selection=json.loads(a.selection.read_text())
unique={l['digest']:l['bytes'] for im in images.values() for l in im.get('layers',[])}
assert sum(unique.values()) < 1960000000, 'Leave at least 40 MB for source and metadata within 2 GB.'
results=[]
deadline=time.monotonic()+3600
def run(cmd,log,timeout):
    start=time.monotonic()
    with log.open('w') as out:
        try:
            r=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,timeout=max(1,min(timeout,deadline-time.monotonic())))
            rc=r.returncode;timed_out=False
        except subprocess.TimeoutExpired:
            rc=None;timed_out=True
    return {'returncode':rc,'timed_out':timed_out,'seconds':round(time.monotonic()-start,3),'log':str(log),'command':cmd}
@dataclasses.dataclass
class File:
    path:str
    name:str
    content:str
for task in selection['tasks']:
    key=task['repo']+'-'+str(task['number']);folder=a.root/key;folder.mkdir(exist_ok=True)
    r=records[task['id']]; im=images[task['id']]
    row={'id':task['id'],'status':'not_run','image_digest':im['platform_digest'],'phases':{}}
    results.append(row)
    if time.monotonic()>=deadline:
        row['status']='resource_blocked';row['reason']='one-hour replay driver budget exhausted'
        (a.root/'native_runs.json').write_text(json.dumps(results,indent=2)+'\n')
        continue
    immutable=task['image'].split(':')[0]+'@'+im['platform_digest']
    pull=run(pod+['pull','--platform','linux/amd64',immutable],folder/'pull.log',1200)
    row['pull']=pull
    if pull['returncode']!=0:
        row['status']='resource_blocked';row['reason']='immutable image pull failed'
    else:
        source=a.upstream/f"hwe_bench/harness/repos/verilog/{task['repo']}/{task['repo']}.py"
        tree=ast.parse(source.read_text())
        method=next(n for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='runtime_files')
        ns={'File':File};exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(source),'exec'),ns)
        files=ns['runtime_files'](types.SimpleNamespace(pr=types.SimpleNamespace(**r)))
        runtime=folder/'private-runtime';runtime.mkdir(exist_ok=True)
        for f in files:(runtime/f.name).write_text(f.content)
        (runtime/'fix.patch').write_text(r['fix_patch']);(runtime/'test.patch').write_text(r['test_patch'])
        volumes=[]
        for f in runtime.iterdir():volumes+=['-v',f'{f}:/home/{f.name}:ro']
        # Rootless conmon/runtime inherit explicit four-core affinity; no host secrets or proxies.
        base=['taskset','-c',cpus]+pod+['run','--rm','--network','none','--http-proxy=false','--pids-limit','512','--memory','16g',
             '-e','MAKEFLAGS=-j4','-e','NUM_JOBS=4','-e','OMP_NUM_THREADS=4']+volumes
        for phase,script in [('base','test-run.sh'),('reference','fix-run.sh')]:
            name='hwe-'+key+'-'+phase
            row['phases'][phase]=run(base+['--name',name,immutable,'bash','/home/'+script],folder/(phase+'.log'),1200)
            if row['phases'][phase]['timed_out']:
                subprocess.run(pod+['rm','-f',name],capture_output=True)
        probe='cd /home/'+task['repo']+'; printf "BASELINE "; git rev-parse HEAD; printf "ANCESTOR_COUNT "; git rev-list --count HEAD; printf "REMOTES\\n"; git remote -v; printf "TOOLS\\n"; verilator --version 2>/dev/null || true; python --version 2>/dev/null || true; git --version; printf "LEAK_FILES\\n"; find /home -maxdepth 2 -type f \\( -name "*patch*" -o -name "tb_script.sh" -o -name "prepare.sh" \\) -print'
        row['image_audit']=run(['taskset','-c',cpus]+pod+['run','--rm','--network','none','--http-proxy=false',immutable,'bash','-lc',probe],folder/'image-audit.log',90)
        row['status']='reference_calibration'
        row['reason']='raw runs complete; adjudication must inspect simulation outcomes, patch application, and infrastructure separately'
    (a.root/'native_runs.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({k:v for k,v in row.items() if k not in ['phases','pull','image_audit']}),flush=True)
