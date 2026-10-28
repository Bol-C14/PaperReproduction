raise SystemExit("Historical entry point preserved in git history; use check_harness_hardening.py in a fresh result layout. Legacy reports describe historical executions, not a new rerun.")
"""Eight fixed boundary/control trials; no generated model code or API calls."""
import hashlib,json,pathlib,subprocess
from container_isolation import run_reviewed,IMAGE,ENV,payload_provenance
root=pathlib.Path(__file__).resolve().parents[1]/'isolation_validation'
root.mkdir(exist_ok=True)
canary=pathlib.Path('/workspace/fixme-owned-isolation-canary.txt');canary.write_text('synthetic-boundary-canary-not-a-secret\n')
probes={
 'filesystem':f'test ! -e {canary} && test ! -e /var/run/docker.sock && test ! -e /workspace/PaperReproduction/.git && echo BOUNDARY_OK',
 'root_readonly':'if touch /root-write-probe 2>/dev/null; then exit 1; fi; echo READONLY_OK',
 'scratch_positive':'echo scratch > /work/probe; test "$(cat /work/probe)" = scratch && echo SCRATCH_OK',
 'uid_caps_privileges':'test "$(id -u)" = 65534 && grep -q "CapEff:[[:space:]]*0000000000000000" /proc/self/status && grep -q "NoNewPrivs:[[:space:]]*1" /proc/self/status && echo PRIVILEGES_OK',
 'network':'test -z "$(ip route)" && if wget -T 1 -q -O /work/network http://192.0.2.1/; then exit 1; fi; echo NETWORK_NONE_OK',
 'environment':'test -z "$NR_KEY" && test -z "$OPENAI_API_KEY" && test -z "$VALIDITY_SYNTHETIC_CANARY" && echo ENV_ALLOWLIST_OK',
 'intentional_failure':'echo EXPECTED_NEGATIVE; exit 7',
 'timeout':'echo TIMEOUT_STARTED; sleep 5; echo UNEXPECTED_FINISH',
}
expected=['BOUNDARY_OK','READONLY_OK','SCRATCH_OK','PRIVILEGES_OK','NETWORK_NONE_OK','ENV_ALLOWLIST_OK']
rows=[]
for i,(label,script) in enumerate(probes.items()):
 data=(script+'\n').encode();(root/(label+'.sh')).write_bytes(data)
 r=run_reviewed({'probe.sh':data},['sh','/work/probe.sh'],timeout=1 if label=='timeout' else 5)
 r.update(label=label,fixture_sha256=hashlib.sha256(data).hexdigest());(root/(label+'.json')).write_text(json.dumps(r,indent=2)+'\n');rows.append(r)
 if i<6:assert r['status']=='completed' and r['returncode']==0 and expected[i] in r['stdout'],r
 elif label=='intentional_failure':assert r['status']=='completed' and r['returncode']==7,r
 else:assert r['status']=='timeout' and 'UNEXPECTED_FINISH' not in r['stdout'],r
 assert r['container_removed'],r
assert canary.read_text()=='synthetic-boundary-canary-not-a-secret\n'
local=payload_provenance('model_generated');assert local['execution_requires_review'] and not local['external_transmission_permitted']
summary={'trials':len(rows),'boundary_checks':6,'negative_controls':2,'all_checks_passed':True,'image':IMAGE,'model_calls':0,'paid_resources':0,'host_configuration_changes':False,'host_canary_unchanged':True,'future_model_provenance_default':local,'scope':'fixed reviewed BusyBox shell probes; no generated code, no HDL toolchain validation','seconds_sum':round(sum(r['seconds'] for r in rows),4)}
(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
