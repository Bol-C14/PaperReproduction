"""Single logging-only 160-step replay; frozen main experiment is untouched."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

p = Path(__file__).resolve().parent
out = p / 'runs/supplemental_logging'
if (out / 'record.json').exists():
    raise SystemExit('Supplement already recorded; refusing retry')
case = p / 'runs/attempt1/delayed_pulse/novel_bound160'
record = dict(amendment_commit='e70f6cc',
              started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              inputs_sha256={name: hashlib.sha256((case/name).read_bytes()).hexdigest()
                             for name in ['gold.v','candidate.v','top.ys']})
inner = """import json,subprocess,time
from pathlib import Path
p=Path('/out'); start=time.monotonic()
r=subprocess.run(['stdbuf','-o0','yosys','-s','top.ys'],capture_output=True,text=True,timeout=150)
(p/'yosys.stdout.log').write_text(r.stdout)
(p/'yosys.stderr.log').write_text(r.stderr)
(p/'command_result.json').write_text(json.dumps(dict(argv=['stdbuf','-o0','yosys','-s','top.ys'],returncode=r.returncode,wall_seconds=time.monotonic()-start),indent=2))
(p/'container_memory_peak_bytes.txt').write_text(Path('/sys/fs/cgroup/memory.peak').read_text())
(p/'container_cpu.stat').write_text(Path('/sys/fs/cgroup/cpu.stat').read_text())
"""
cmd=['docker','run','--rm','--network=none','--user=1000:1000','--read-only',
     '--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=128',
     '--cpus=2','--memory=4g','--memory-swap=4g','--tmpfs','/tmp:rw,noexec,nosuid,size=256m',
     '--mount',f'type=bind,src={case},dst=/case,readonly',
     '--mount',f'type=bind,src={out},dst=/out','--workdir=/case',
     'sha256:9805c8192b5a06fb39955367d95c372ace0dca0b934ae803d92d90235f9f7383',
     'python3','-c',inner]
record['container_argv']=cmd
(out/'record.json').write_text(json.dumps(record,indent=2))
start=time.monotonic()
r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
(out/'container.stdout.log').write_text(r.stdout)
(out/'container.stderr.log').write_text(r.stderr)
record.update(container_returncode=r.returncode,container_wall_seconds=time.monotonic()-start,
              completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
if (out/'yosys.stdout.log').exists():
    frames=[]
    for line in (out/'yosys.stdout.log').read_text().splitlines():
        parts=line.split()
        if len(parts)==5 and parts[0].isdigit() and parts[1].endswith('trigger') and parts[2]=='1':
            frames.append(int(parts[0]))
    record['first_asserted_trigger_in_returned_witness']=min(frames) if frames else None
(out/'record.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='container_argv'},indent=2))
