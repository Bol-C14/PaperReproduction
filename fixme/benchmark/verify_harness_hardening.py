"""Offline evidence verification only; no Docker/model/tool invocation."""
import json,pathlib,hashlib
from fixed_oracle import evaluate_fixed,_evaluate_bound_result
from container_isolation import MANIFEST,MANIFEST_SHA256,authorize_fixture
p=pathlib.Path(__file__).resolve().parents[1]/'harness_hardening'
assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest()==MANIFEST_SHA256
plan=json.loads((p/'PLAN.json').read_text());manifest=json.loads(MANIFEST.read_text());summary=json.loads((p/'results/summary.json').read_text());assert len(summary['trials'])==13
for t in plan['trials']:
 e=manifest['fixtures'][t['id']];d=p/t['directory'];files={n:(d/n).read_bytes() for n in e['files']};authorize_fixture(files,e['argv'],e['timeout'],'reviewed_local_fixture',t['id'])
 r=json.loads((p/'results'/(t['id'].split('/')[-1]+'.json')).read_text());assert r['container']['container_removed'];assert evaluate_fixed(r['container'])['status']==t['expected'];assert r['decision']['status']==t['expected']
assert len(summary['pre_execution_rejections'])==6 and len(summary['synthetic_taxonomy_tests'])==6
for t in summary['synthetic_taxonomy_tests']:
 envelope={'status':'completed','returncode':0,'oracle_policy':'trusted_fixed_mux_trace','stdout':json.dumps({'compile':t['synthetic_compile_state']})};assert _evaluate_bound_result(envelope)==t['decision']
assert evaluate_fixed({'status':'completed','returncode':0,'oracle_policy':'trusted_fixed_mux_trace','stdout':'CHECK_PASS checks=4'})['status']=='unknown'
print('PASS: 13 saved fixed executions, six pre-execution rejections, six synthetic taxonomy controls; manifest/hash/recipe binding and oracle authority checked offline')
