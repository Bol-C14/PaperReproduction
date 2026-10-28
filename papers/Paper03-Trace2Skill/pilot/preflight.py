#!/usr/bin/env python3
"""Read-only, no-credential, no-network canary resource check. Never starts a pilot."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from chat_adapter import BASE_URL,MODEL,SECRET_ENV,EXPIRES,LIVE_ENABLED,Limits,worker_environment
P=Path(__file__).resolve().parents[1]
def check():
    now=dt.datetime.now(dt.timezone.utc)
    tools={x:shutil.which(x) for x in ['docker','iverilog','vvp','verilator','yosys','ollama']}
    for name in ['iverilog','vvp']:
        candidate=Path('/workspace/free-tools/bin')/name
        if not tools[name] and candidate.is_file():tools[name]=str(candidate)
    docker={}
    if tools['docker']:
        with tempfile.TemporaryDirectory(prefix='t2s-resource-') as d:
            for label,args in [('version',['docker','version','--format','{{.Server.Version}}']),('images',['docker','image','ls','--format','{{.Repository}}:{{.Tag}}'])]:
                try:
                    r=subprocess.run(args,env=worker_environment(Path(d)),capture_output=True,text=True,timeout=10,check=False)
                    docker[label]={'exit_code':r.returncode,'value':r.stdout.strip() if r.returncode==0 else 'unavailable; error text omitted'}
                except (OSError,subprocess.TimeoutExpired):docker[label]={'status':'unavailable'}
    dependencies={m:importlib.util.find_spec(m) is not None for m in ['openai','ray','pytest','yaml','pydantic']}
    data=Path('/tmp/t2s-cvdp-pilot-source.jsonl')
    dataset={'revision':'5b807d945f6a99aa645f7e43a64a2115e281b4bf','download_status':'HTTP403; stopped; no alternate access attempt', 'present':data.is_file(), 'expected_sha256':'809916fa3248a4b2597b2a2ac364d3450d24936cad0e25bbe1bf0f1243ad1ea7'}
    if data.is_file():dataset['sha256_matches']=hashlib.sha256(data.read_bytes()).hexdigest()==dataset['expected_sha256']
    report={'checked_at_utc':now.isoformat(),'python':platform.python_version(),'tools':tools,'docker':docker,'dependencies':dependencies,'dataset':dataset,'model':MODEL,'base_url':BASE_URL,'api':'Chat Completions only; never probed','expiry_utc':EXPIRES.isoformat(),'seconds_until_expiry':(EXPIRES-now).total_seconds(),'live_enabled':LIVE_ENABLED,'credential_status':'presence-only boolean; value never read; not configured', 'NR_KEY_present':(SECRET_ENV in os.environ), 'target_domain_authorization':'unknown; no domain-specific metadata surfaced; not probed','provider_account_quota':{'tokens_per_day':5000000,'rpm':60,'tpm':500000,'concurrency':4,'scope':'entire account shared; NOT allocated to this canary'},'proposed_local_limits':Limits().__dict__,'budget_approval':'pending parent activation; zero reserved from account','vault_scope':'All environments explicitly accepted by user; no narrowing required','alternate_real_rtl_fixture':{'source':'cocotb/cocotb v1.9.2 CC0 adder','is_original_cvdp_task':False,'smoke_status':'NOT_RUN; iverilog/vvp missing'},'readiness':'NO_GO','blockers':['real pinned task bytes inaccessible (HTTP403)','no simulator executable or prepared verifier image','NeMo Gym live dependencies missing; Responses-based agent not wired to this Chat-only offline adapter','no verified input token counter/chat-template revision; cannot admit a live call','no reviewed live transport/parent activation; LIVE_ENABLED=False','NR_KEY not safely provisioned; task never accesses credentials'],'real_model_requests':0,'real_verifier_executions':0}
    verified=P/'metrics/verified_toolchain.json'
    if verified.is_file():
        report['verified_local_toolchain']=json.loads(verified.read_text())
        report['real_verifier_executions']=report['verified_local_toolchain']['total_actual_rtl_simulations']
        report['alternate_real_rtl_fixture']['smoke_status']='actual host and isolated Docker controls passed; see recorded hashes/times'
        report['blockers']=[b for b in report['blockers'] if 'no simulator executable' not in b]
        report['readiness']='INFRASTRUCTURE_SMOKE_READY; LIVE_AND_CVDP_NOT_READY'
    (P/'metrics/pilot_preflight.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report
if __name__=='__main__':check()
