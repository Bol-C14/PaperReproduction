"""Bounded G3 calibration PORT using upstream Harbor environment/agents/verifier.
Not a leaderboard runner. Never pass this auditor's task directory to a live agent.
"""
import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import time
import traceback

from harbor.agents.nop import NopAgent
from harbor.agents.oracle import OracleAgent
from harbor.environments.podman import PodmanEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.task.task import Task
from harbor.models.trial.config import ResourceMode
from harbor.models.trial.paths import TrialPaths
from harbor.verifier.verifier import Verifier

ROOT = Path(os.environ['REPRO_ROOT']).expanduser().resolve()
HERE = Path(__file__).resolve().parent
ASSETS = ROOT/'assets/terminal-bench'
RESULTS = ROOT/'results/terminal-bench/run-v7'
DATA = ROOT/'checkouts/terminal-bench/dataset'
TASKS = ['log-summary-date-ranges', 'regex-log', 'cancel-async-tasks']
OUTPUT = dict(zip(TASKS, ['summary.csv', 'regex.txt', 'run.py']))


class AffinityPort(PodmanEnvironment):
    """Only change: every execution command starts with verified in-container affinity.
    This is cooperative affinity, not a hostile-agent CPU quota security boundary.
    """
    affinity = '0'
    async def upload_dir(self, source_dir, target_dir):
        r = await self.exec('mkdir -p '+shlex.quote(target_dir),timeout_sec=30)
        if r.return_code: raise RuntimeError('Cannot create upload directory')
        cid = await self._platform._resolve_service_container('main')
        await self._platform._engine_cp(str(source_dir)+'/.',cid+':'+target_dir)

    async def upload_file(self, source_path, target_path):
        cid = await self._platform._resolve_service_container('main')
        await self._platform._engine_cp(str(source_path),cid+':'+target_path)

    async def exec(self, command, **kwargs):
        wrapped = f'taskset -c {self.affinity} bash -c {shlex.quote(command)}'
        result = await super().exec(wrapped, **kwargs)
        self.command_log.append({'command':command, 'return_code':result.return_code,
                                 'stdout':result.stdout, 'stderr':result.stderr})
        return result


def make_ports():
    for name in TASKS:
        dst=ASSETS/'ports'/name
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(DATA/name,dst)
        config=(dst/'task.toml').read_text()
        config=re.sub(r'docker_image = .*', f'docker_image = "localhost/g3-{name}:calibration"',config)
        (dst/'task.toml').write_text(config)
        # No test assertions are changed. Dependency setup already completed online.
        launch='#!/bin/bash\ncd /app\n'
        if name=='cancel-async-tasks': launch+='cp /tests/test.py /app/test.py\n'
        launch+='python -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA\nrc=$?\nif [ "$rc" -eq 0 ]; then echo 1; else echo 0; fi > /logs/verifier/reward.txt\n'
        (dst/'tests/test.sh').write_text(launch)
        if name=='log-summary-date-ranges':
            p=dst/'solution/solve.sh'
            p.write_text(p.read_text().replace('apt-get update && apt-get install -y grep coreutils','\n# Dependency installation moved to image preparation.'))
    overlay=ASSETS/'offline-overlay.yaml'
    overlay.write_text('services:\n  main:\n    network_mode: none\n    cap_drop: [ALL]\n    security_opt: [no-new-privileges:true]\n    pids_limit: 128\n')
    return overlay


def alternative_pattern():
    octet=r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])'
    ip=rf'(?<![0-9A-Za-z])(?:{octet}\.){{3}}{octet}(?![0-9A-Za-z])'
    date=r'[0-9]{4}-(?:(?:01|03|05|07|08|10|12)-(?:0[1-9]|[12][0-9]|3[01])|(?:04|06|09|11)-(?:0[1-9]|[12][0-9]|30)|02-(?:0[1-9]|1[0-9]|2[0-9]))'
    return rf'^(?=[^\n]*{ip})[^\n]*(?<![0-9A-Za-z])({date})(?![0-9A-Za-z])'


async def trial(name, agent_name, cpus, overlay):
    ident=f'{name}-{agent_name}-affinity{cpus}'
    dest=RESULTS/ident
    if dest.exists(): raise RuntimeError(f'Refuse overwrite: {dest}')
    paths=TrialPaths(dest);paths.mkdir()
    task=Task(ASSETS/'ports'/name)
    logger=logging.getLogger(ident)
    handler=logging.FileHandler(dest/'harness.log');logger.addHandler(handler);logger.setLevel(logging.DEBUG)
    env=AffinityPort(environment_dir=task.paths.environment_dir,environment_name='g3-'+name,
        session_id=ident,trial_paths=paths,task_env_config=task.config.environment,
        cpu_enforcement_policy=ResourceMode.IGNORE,override_memory_mb=2048,
        extra_docker_compose=[overlay],logger=logger,auto_mounting=False,
        enable_environment_dir_upload=False)
    env.affinity='0' if cpus==1 else '0,1';env.command_log=[]
    result={'id':ident,'task':name,'agent':agent_name,'cpu_affinity':env.affinity,'memory_mb':2048,
            'status':'not_run','port':True,'timings_sec':{},'timeouts':[]}
    start=time.monotonic()
    try:
        await asyncio.wait_for(env.start(force_build=False),timeout=600)
        result['timings_sec']['environment']=time.monotonic()-start
        pre=await env.exec("python - <<'INNER'\nimport os,json,pathlib,hashlib,socket\np=pathlib.Path('/app')\nprint(json.dumps({'affinity':sorted(os.sched_getaffinity(0)),'memory_max':pathlib.Path('/sys/fs/cgroup/memory.max').read_text().strip(),'pids_max':pathlib.Path('/sys/fs/cgroup/pids.max').read_text().strip(),'controllers':pathlib.Path('/sys/fs/cgroup/cgroup.controllers').read_text().strip(),'status':[x for x in pathlib.Path('/proc/self/status').read_text().splitlines() if x.startswith(('CapEff:','NoNewPrivs:'))],'hidden_paths':{x:pathlib.Path(x).exists() for x in ['/tests/test_outputs.py','/solution/solve.sh','/app/summary.csv','/app/regex.txt','/app/run.py','/var/run/docker.sock','__HOST_HOME_PROBE__']},'inputs':{str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.rglob('*')) if f.is_file()},'interfaces':os.listdir('/sys/class/net'),'python':__import__('sys').version}))\nINNER".replace("'__HOST_HOME_PROBE__'", repr(os.environ["HOST_HOME_PROBE"])),timeout_sec=30)
        limits=json.JSONDecoder().raw_decode(pre.stdout[pre.stdout.index('{"affinity"'):].strip())[0]; result['preflight']=limits
        if limits['affinity']!=list(range(cpus)) or limits['memory_max']!='2147483648' or limits['pids_max']!='128': raise RuntimeError('Limits not enforced')
        if limits['interfaces']!=['lo'] or any(limits['hidden_paths'].values()): raise RuntimeError('Unexpected network or hidden/artifact exposure')
        tick=time.monotonic()
        if agent_name in ('oracle','nop'):
            agent=(OracleAgent(logs_dir=paths.agent_dir,task_dir=task.paths.task_dir,trial_paths=paths,agent_timeout_sec=900)
                   if agent_name=='oracle' else NopAgent(logs_dir=paths.agent_dir))
            await agent.setup(env)
            await asyncio.wait_for(agent.run(task.instruction,env,AgentContext()),900)
        else:
            pattern=alternative_pattern()
            await env.exec('printf %s '+shlex.quote(pattern)+' > /app/regex.txt',timeout_sec=30)
        result['timings_sec']['solution']=time.monotonic()-tick
        if agent_name=='nop':
            await env.exec('mkdir -p /logs/verifier; echo 1 > /logs/verifier/reward.txt',timeout_sec=10)
            result['stale_reward_seeded']=1
        artifact=OUTPUT[name]
        try: await env.download_file('/app/'+artifact,dest/artifact)
        except Exception as exc: result['artifact_download_error']=str(exc)
        tick=time.monotonic()
        verdict=await asyncio.wait_for(Verifier(task,paths,env).verify(),900)
        result['timings_sec']['verifier']=time.monotonic()-tick
        result['verifier']=verdict.model_dump(mode='json')
        ctrf_path=paths.verifier_dir/'ctrf.json'
        if ctrf_path.exists(): result['ctrf']=json.loads(ctrf_path.read_text())
        await env.upload_file(HERE/'independent_check.py','/app/auditor_check.py')
        independent=await env.exec('python /app/auditor_check.py '+name,timeout_sec=30)
        result['independent']=json.JSONDecoder().raw_decode(independent.stdout[independent.stdout.index('{"passed"'):].strip())[0]
        result['independent_exit']=independent.return_code
        if (dest/artifact).exists(): result['artifact_sha256']=hashlib.sha256((dest/artifact).read_bytes()).hexdigest()
        result['status']='reference_calibration' if agent_name=='oracle' else 'offline_replay'
        # Harmless timeout liveness probe stays inside one disposable no-op container.
        if name=='regex-log' and agent_name=='nop' and cpus==1:
            tick=time.monotonic()
            try:
                r=await env.exec('sleep 2; touch /app/late-marker',timeout_sec=1)
                result['timeout_probe']={'returned':True,'return_code':r.return_code}
            except Exception as exc:
                result['timeout_probe']={'returned':False,'exception':repr(exc)}
            result['timeout_probe']['elapsed_sec']=time.monotonic()-tick
            await asyncio.sleep(2.5)
            r=await env.exec('test -e /app/late-marker',timeout_sec=10)
            result['timeout_probe']['late_marker_exists']=r.return_code==0
    except Exception as exc:
        result['status']='resource_blocked';result['error']=repr(exc);result['traceback']=traceback.format_exc()
        if isinstance(exc,TimeoutError): result['timeouts'].append({'phase':'outer','elapsed_sec':time.monotonic()-start})
    finally:
        try: await asyncio.wait_for(env.stop(delete=False),60)
        except Exception as exc: result['cleanup_error']=repr(exc)
        result['timings_sec']['total']=time.monotonic()-start
        (dest/'commands.json').write_text(json.dumps(env.command_log,indent=2))
        (dest/'result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({k:result.get(k) for k in ['id','status','error','verifier','independent','timings_sec']}),flush=True)
        handler.close();logger.removeHandler(handler)
    return result


async def main():
    RESULTS.mkdir(exist_ok=True)
    overlay=make_ports()
    results=[]
    for cpus in [1,2]:
        for name in TASKS:
            for agent in ['nop','oracle']:
                results.append(await trial(name,agent,cpus,overlay))
                if results[-1]['status']=='resource_blocked':
                    (RESULTS/'summary.json').write_text(json.dumps(results,indent=2))
                    return
    results.append(await trial('regex-log','alternative',1,overlay))
    (RESULTS/'summary.json').write_text(json.dumps(results,indent=2))


if __name__=='__main__': asyncio.run(main())
