import os,pathlib,subprocess,json,time,hashlib
from container_cleanup import stop_owned_container
r=pathlib.Path(os.environ['E4_WORK_ROOT']);o=r/'results/fluxbench/route1200-v1';prior=r/'results/fluxbench/physical-v1';data=r/'assets/pdagent/dataset/PlaceReasoner-Bench/bp_fe'
assert not o.exists(), 'Inspect uncertain existing results instead of retrying'
assert hashlib.sha256((prior/'cts.odb').read_bytes()).hexdigest()=='8e354cbf16135268c6608838b01f79aec0b5b2f3f6db93673146925b5405406a'
assert hashlib.sha256((prior/'port.sdc').read_bytes()).hexdigest()=='17f7b8fa4b3f81cae2c1480e9344a261e381b8de51164e795e7c6491f89d4d42'
o.mkdir();(o/'port.sdc').write_bytes((prior/'port.sdc').read_bytes())
s=(prior/'routing-recovery.tcl').read_text().replace('read_db /out/cts.odb','read_db /prior/cts.odb')
s=s.replace('detailed_route -output_drc','write_db /out/global-route.odb\ndetailed_route -output_drc')
(o/'routing.tcl').write_text(s)
cpus=','.join(str(x) for x in sorted(os.sched_getaffinity(0))[:4]);image='080c40706b37fb2fece6a61412d17c0e025ee87af82af28e79aa90f5d02a78ac';name='e4-fluxbench-route1200-v1'
cmd=['taskset','-c',cpus,'podman','run','--name',name,'--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--pids-limit=128','--memory=8g','--tmpfs=/tmp:rw,noexec,nosuid,size=128m','-e','OMP_NUM_THREADS=4','-e','QT_QPA_PLATFORM=minimal','-v',str(data)+':/data:ro','-v',str(prior)+':/prior:ro','-v',str(o)+':/out:rw',image,'-no_init','-exit','/out/routing.tcl']
start=time.time();t=time.monotonic();cleanup=None
(o/'started.json').write_text(json.dumps(dict(start_unix=start,command=cmd,timeout_seconds=1200,threads=4,paid_cost_usd=0),indent=2)+'\n')
try:
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=1200);text=p.stdout;code=p.returncode;timeout=False
except subprocess.TimeoutExpired as e:
 text=e.stdout or b'';code=None;timeout=True;cleanup=stop_owned_container(name,o,'/out/routing.tcl')
(o/'routing.log').write_bytes(text)
artifacts={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in o.iterdir() if p.suffix in ['.odb','.def','.v','.sdc','.drc','.tcl','.guide']}
(o/'result.json').write_text(json.dumps(dict(command=cmd,start_unix=start,end_unix=time.time(),seconds=time.monotonic()-t,returncode=code,timeout=timeout,cleanup=cleanup,threads=4,paid_cost_usd=0,artifacts=artifacts,correctness='unverified until independent artifact checks; negative timing remains failure'),indent=2)+'\n')
