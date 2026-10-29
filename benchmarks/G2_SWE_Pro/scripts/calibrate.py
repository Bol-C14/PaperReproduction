"""SWE-Pro-only rootless Podman port. No model or agent; fresh grader per diff.
Reference/hidden files enter only the grader. No home, secrets or socket mounts.
"""
import ast,hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(os.environ['G2_ROOT'])
SRC=ROOT/'checkouts/swe-pro/v2/tasks'; ASSET=ROOT/'assets/swe-pro'; OUT=ROOT/'results/swe-pro'/os.environ.get('G2_RUN','verified-port')
OUT.mkdir(exist_ok=True)
WRAP="import os,sys; os.sched_setaffinity(0,{0,1,2,3}); os.execvp(sys.argv[1],sys.argv[1:])"
results=[];start=time.monotonic()
def run(args,log,timeout=3000):
    with log.open('ab') as f:
        f.write(('\nCOMMAND '+repr(args)+'\n').encode());f.flush()
        return subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=timeout).returncode
images=json.loads((ASSET/'oci/summary.json').read_text())
variants=os.environ.get('G2_VARIANTS','reference,empty').split(',')
if any(v not in {'reference','empty','partial','alternative'} for v in variants):raise SystemExit('Unsupported G2 control variant')
if set(variants)&{'partial','alternative'}:
    baselines=json.loads(Path(os.environ['G2_BASELINE_FILE']).read_text())
    gate_tasks={r['task'] for r in images}
    amendment_path=os.environ.get('G2_GATE_AMENDMENT')
    if amendment_path:
        amendment=json.loads(Path(amendment_path).read_text())
        if set(amendment['cohort'])!=gate_tasks or amendment['denominator']!=4:raise SystemExit('Amended G2 cohort mismatch')
        eligible=set(amendment['eligible']);blocked=set(amendment['blocked'])
        if len(eligible)!=3 or len(blocked)!=1 or eligible&blocked or eligible|blocked!=gate_tasks:raise SystemExit('Invalid G2 gate amendment')
        if set(os.environ.get('G2_TASKS','').split(','))!=eligible:raise SystemExit('G2 amended task scope mismatch')
        if set(variants)!={'partial','alternative'}:raise SystemExit('G2 amendment covers candidates only')
        if any(r['status']!='resource_blocked' for r in baselines if r['task'] in blocked):raise SystemExit('G2 excluded task state changed; audit first')
        if len([r for r in baselines if r['task'] in blocked])!=2:raise SystemExit('G2 blocked baseline pair missing')
        for row in images:
            if row['digest']!=amendment['pinned_images'][row['task']]:raise SystemExit('G2 pinned image changed')
            for path,digest in amendment['selected_test_hashes'][row['task']].items():
                if hashlib.sha256((SRC/row['task']/path).read_bytes()).hexdigest()!=digest:raise SystemExit('G2 hidden verifier changed')
        gate_tasks=eligible
    for row in images:
        if row['task'] not in gate_tasks:continue
        for v in ['reference','empty']:
            matches=[r for r in baselines if r['task']==row['task'] and r['variant']==v]
            if len(matches)!=1 or matches[0]['status']!='reference_calibration' or matches[0]['resolved']!=(v=='reference'):
                raise SystemExit('G2 baseline gate incomplete; no candidate grader launched')
    patch_root=Path(os.environ['G2_PATCH_ROOT'])
    frozen=json.loads((patch_root/'candidate_manifest.json').read_text())
for row in images:
    task=row['task'];t=SRC/task
    if os.environ.get('G2_TASKS') and task not in os.environ['G2_TASKS'].split(','):continue
    for variant in variants:
        d=OUT/task/variant
        if (d/'record.json').exists():
            results.append(json.loads((d/'record.json').read_text()));continue
        d.mkdir(parents=True,exist_ok=True);(d/'verifier').mkdir(exist_ok=True)
        log=d/'native.log';name='g2v-'+task.split('-')[1][:8]+'-'+variant
        rec={'task':task,'variant':variant,'status':'not_run'};results.append(rec)
        if os.environ.get('G2_GATE_AMENDMENT'):
            rec['gate_amendment_sha256']=hashlib.sha256(Path(os.environ['G2_GATE_AMENDMENT']).read_bytes()).hexdigest()
            rec['selected_denominator']=4;rec['conditional_cases']=3
        image='ghcr.io/scaleapi/swe-bench_pro-v2@'+row['digest']
        if variant in {'partial','alternative'}:
            patch=(patch_root/task/(variant+'.diff')).read_text()
            expected=next(r['patch_sha256'] for r in frozen if r['task']==task and r['variant']==variant)
            if hashlib.sha256(patch.encode()).hexdigest()!=expected:raise SystemExit('Frozen G2 candidate hash mismatch')
            if amendment_path:
                pinned=next(r['patch_sha256'] for r in amendment['frozen_candidates'] if r['task']==task and r['variant']==variant)
                if pinned!=expected:raise SystemExit('G2 amendment candidate hash mismatch')
        else:patch=(t/'solution/gold_patch.diff').read_text() if variant=='reference' else ''
        (d/'model.patch').write_text(patch);rec['patch_sha256']=hashlib.sha256(patch.encode()).hexdigest()
        try:
            if subprocess.run(['podman','image','exists',image]).returncode:
                rec.update(status='resource_blocked',reason='image unavailable; inspect recorded pull outcome');continue
            if time.monotonic()-start>5400:
                rec.update(status='resource_blocked',reason='bounded execution wallclock');continue
            args=['podman','create','--name',name,'--network','none','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','4g','--pids-limit','512','--env','OMP_NUM_THREADS=4','--env','OPENBLAS_NUM_THREADS=4','--volume',str(d/'verifier')+':/logs/verifier:rw,Z','--entrypoint','python3',image,'-c',"import os; os.sched_setaffinity(0,{0,1,2,3}); os.execl('/bin/sleep','sleep','infinity')"]
            if run(args,log,60) or run(['podman','start',name],log,60):
                rec.update(status='resource_blocked',reason='rootless OCI create/start failed');continue
            fix=task.split('-')[1]
            probe=f"id; grep Cpus_allowed_list /proc/self/status; cd /app 2>/dev/null || cd /testbed; echo HEAD=$(git rev-parse HEAD); echo FIX_OBJECT=$(git cat-file -t {fix} 2>/dev/null || echo absent); git for-each-ref; git reflog; git stash list; git fsck --unreachable --no-reflogs; ls -d /solution /tests 2>/dev/null; python3 -c \"import socket; s=socket.socket(); s.settimeout(3); print('NETWORK_CONNECT',s.connect_ex(('1.1.1.1',443)))\""
            run(['podman','exec',name,'python3','-c',WRAP,'bash','-c',probe],d/'isolation.log',120)
            if 'Cpus_allowed_list:\t0-3' not in (d/'isolation.log').read_text():
                rec.update(status='resource_blocked',reason='affinity check failed');continue
            rec['verified_cpus']='0-3'
            if patch:
                if run(['podman','cp',str(d/'model.patch'),name+':/tmp/model.patch'],log,60):raise RuntimeError('patch copy failed')
                rc=run(['podman','exec',name,'python3','-c',WRAP,'bash','-c','cd /app 2>/dev/null || cd /testbed; git apply --verbose /tmp/model.patch'],log,120)
                rec['apply_rc']=rc
                if rc:rec.update(reason='patch application failure');continue
            if os.environ.get('G2_SEMANTIC_CHECK'):
                run(['podman','cp',os.environ['G2_SEMANTIC_CHECK'],name+':/tmp/g2-semantic.py'],log,60)
                rec['semantic_probe_rc']=run(['podman','exec',name,'python3','-c',WRAP,'python3','/tmp/g2-semantic.py',task],d/'semantic.log',120)
                lines=(d/'semantic.log').read_text().splitlines()
                markers=[line[len('SEMANTIC_RESULT='):] for line in lines if line.startswith('SEMANTIC_RESULT=')]
                rec['semantic_probe']=json.loads(markers[-1]) if markers else {'status':'probe_error; inspect private log'}
            if run(['podman','cp',str(t/'tests'),name+':/tests'],log,60):raise RuntimeError('verifier copy failed')
            rec['verifier_rc']=run(['podman','exec',name,'python3','-c',WRAP,'bash','/tests/test.sh'],log,3000)
            cfg=json.loads((t/'tests/config.json').read_text())
            parse=lambda x:ast.literal_eval(x) if isinstance(x,str) else x
            f2p=set(parse(cfg['fail_to_pass']));p2p=set(parse(cfg['pass_to_pass']));required=f2p|p2p
            output=json.loads((d/'verifier/output.json').read_text());passed={x['name'] for x in output['tests'] if x['status']=='PASSED'}
            rec.update(status='reference_calibration',required=len(required),passed_required=len(required&passed),f2p_passed=len(f2p&passed),p2p_passed=len(p2p&passed),missing=sorted(required-passed),resolved=bool(required) and required<=passed,reward=(d/'verifier/reward.txt').read_text().strip())
        except subprocess.TimeoutExpired as e:rec.update(status='resource_blocked',reason='timeout',timeout_sec=e.timeout)
        except Exception as e:rec.update(status='resource_blocked',reason=repr(e))
        finally:
            if subprocess.run(['podman','container','exists',name]).returncode==0:run(['podman','rm','-f','--time','0',name],log,60)
            (d/'record.json').write_text(json.dumps(rec,indent=2));(OUT/'results.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
