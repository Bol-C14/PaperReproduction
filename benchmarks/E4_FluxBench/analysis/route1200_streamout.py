"""Invoke the byte-pinned official ORFS streamout harness; not signoff."""
import os,pathlib,subprocess,json,time,hashlib
from container_cleanup import stop_owned_container
r=pathlib.Path(os.environ['E4_WORK_ROOT']);o=r/'results/fluxbench/route1200-v1';a=r/'assets/fluxbench/official-nangate';data=r/'assets/pdagent/dataset/PlaceReasoner-Bench/bp_fe';probe=r/'results/fluxbench/nangate-gds-probe-v1'
assert all(x['exact_match'] for x in json.load(open(a/'compatibility.json')))
assert hashlib.sha256((a/'def2stream.py').read_bytes()).hexdigest()=='3d6a851764ab590a55ad51f6726b6954562560c9cd2d098d8bc53caad8a51209'
assert hashlib.sha256((o/'route.def').read_bytes()).hexdigest()==json.load(open(o/'result.json'))['artifacts']['route.def']['sha256']
assert not (o/'streamout.json').exists()
image='5535500ecc23ac660e54e75e873d27cb47a6e05666fc29cbc8f446e8ca6d98ea';name='e4-fluxbench-streamout-v1';cpus=','.join(str(x) for x in sorted(os.sched_getaffinity(0))[:4])
cmd=['taskset','-c',cpus,'podman','run','--name',name,'--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--memory=8g','--tmpfs=/tmp:rw,nosuid,size=128m','-e','QT_QPA_PLATFORM=minimal','-e','OMP_NUM_THREADS=4','-e','GDS_ALLOW_EMPTY=','-v',str(a)+':/assets:ro','-v',str(data)+':/data:ro','-v',str(probe)+':/probe:ro','-v',str(o)+':/out:rw','--entrypoint','/usr/bin/klayout',image,'-b','-rd','tech_file=/probe/portable.lyt','-rd','layer_map=','-rd','in_def=/out/route.def','-rd','design_name=picorv32','-rd','in_files=/assets/NangateOpenCellLibrary.gds','-rd','seal_file=','-rd','out_file=/out/final.gds','-r','/assets/def2stream.py']
t=time.monotonic();cleanup=None
try:p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);output=p.stdout;code=p.returncode;timeout=False
except subprocess.TimeoutExpired as e:output=e.stdout or b'';code=None;timeout=True;cleanup=stop_owned_container(name,o,'/assets/def2stream.py')
(o/'streamout.log').write_bytes(output);g=o/'final.gds'
d=dict(command=cmd,seconds=time.monotonic()-t,returncode=code,timeout=timeout,cleanup=cleanup,gds_bytes=g.stat().st_size if g.exists() else None,gds_sha256=hashlib.sha256(g.read_bytes()).hexdigest() if g.exists() else None,def_sha256=hashlib.sha256((o/'route.def').read_bytes()).hexdigest(),technology_sha256=hashlib.sha256((probe/'portable.lyt').read_bytes()).hexdigest(),source_script_sha256=hashlib.sha256((a/'def2stream.py').read_bytes()).hexdigest(),correctness='Streamout only; independent parser and physical/timing checks required')
(o/'streamout.json').write_text(json.dumps(d,indent=2)+'\n');assert code==0
