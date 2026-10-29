"""Recompute decisions from private parsed tests, never from PASS text/exit alone."""
import argparse,ast,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);a=p.parse_args();d=Path(__file__).resolve().parents[1]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((d/'manifest.json').read_text());attempts=json.loads((d/'attempts.json').read_text());amendment=json.loads((d/'CONDITIONAL_STUDY.json').read_text())
assert len(attempts)==44
for name in ['cpu-controller','host-affinity-missing-logs']:assert sum(x['attempt_batch']==name for x in attempts)==8
assert sum(x['attempt_batch']=='planned-after-four-task-controls' and x['status']=='not_run' for x in attempts)==8
assert amendment['denominator']==4 and len(amendment['eligible'])==3 and len(amendment['blocked'])==1
assert amendment['original_gate_preflight_sha256']==h(d/'logs/gate-preflight.txt')
for task,files in amendment['selected_test_hashes'].items():
 for path,digest in files.items():assert h(a.private/'upstream/v2/tasks'/task/path)==digest
candidates=json.loads((d/'candidate_manifest.json').read_text())
assert len(candidates)==8 and all(r['status']=='not_run' for r in candidates) # frozen preparation-time state
for r in candidates:assert h(a.private/'prepared-candidates'/r['task']/(r['variant']+'.diff'))==r['patch_sha256']
def verify(r):
 folder=a.private/r['evidence_prefix']/r['task']/r['variant']
 cfg=json.loads((a.private/'upstream/v2/tasks'/r['task']/'tests/config.json').read_text());parse=lambda x:ast.literal_eval(x) if isinstance(x,str) else x
 required=set(parse(cfg['fail_to_pass']))|set(parse(cfg['pass_to_pass']));assert required
 tests=json.loads((folder/'verifier/output.json').read_text())['tests'];passed={t['name'] for t in tests if t['status']=='PASSED'}
 resolved=required<=passed
 assert resolved==r['resolved'] and len(required&passed)==r['passed_required'] and len(required)==r['required']
 assert (folder/'verifier/reward.txt').read_text().strip()==str(int(resolved))
 assert h(folder/'model.patch')==r['patch_sha256']
 isolation=(folder/'isolation.log').read_text()
 for evidence in ['Cpus_allowed_list:\t0-3','FIX_OBJECT=absent','NETWORK_CONNECT 101']:assert evidence in isolation
 if r['variant'] in {'partial','alternative'}:
  assert r['gate_amendment_sha256']==h(d/'CONDITIONAL_STUDY.json') and r['selected_denominator']==4 and r['conditional_cases']==3
  assert r['task'] in amendment['eligible']
  frozen=next(x for x in candidates if x['task']==r['task'] and x['variant']==r['variant']);assert frozen['patch_sha256']==r['patch_sha256']
  lines=(folder/'semantic.log').read_text().splitlines();actual=json.loads(next(x[len('SEMANTIC_RESULT='):] for x in reversed(lines) if x.startswith('SEMANTIC_RESULT=')))
  assert actual==r['semantic_probe'] and actual['passed']==all(x['passed'] for x in actual['checks'])
 return {'task':r['task'],'variant':r['variant'],'passed_required':len(required&passed),'required':len(required),'resolved':resolved}
baselines=json.loads((d/'current_baselines.json').read_text());base=[verify(r) for r in baselines if r['status']=='reference_calibration'];assert len(base)==6
assert sum(r['status']=='resource_blocked' for r in baselines)==2
controls=json.loads((d/'conditional_controls.json').read_text());conditional=[verify(r) for r in controls if r['status']=='reference_calibration'];assert len(conditional)==6
assert sum(r['status']=='not_run' and r['task'] in amendment['blocked'] for r in controls)==2
for variant in ['partial','alternative']:
 values=[r for r in conditional if r['variant']==variant];assert len(values)==3
 assert sum(r['resolved'] for r in values)==manifest['results']['conditional_'+variant+'_accepted']
proof=json.loads((d/'semantic_alignment.json').read_text());folder=a.private/'prepared-candidates'/proof['task']
def dump(path):return ast.dump(next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='find_keys'),include_attributes=False)
x=dump(folder/'reference-source/scripts/new-solr-updater.py');assert x==dump(folder/'apply-check-partial/scripts/new-solr-updater.py')
assert hashlib.sha256(x.encode()).hexdigest()==proof['ast_sha256']
pulls=json.loads((d/'image_pull_attempts.json').read_text());assert pulls[0]['exit_code']==125 and pulls[1]['exit_code']==0
assert '120012366' in (a.private/pulls[0]['private_log']).read_text()
for row in json.loads((d/'private_evidence_index.json').read_text()):
 f=a.private/row['path'];assert f.stat().st_size==row['bytes'] and h(f)==row['sha256']
assert manifest['limits']['model_calls']==0
print(json.dumps({'validation':'passed','selected_cases':4,'native_cases':3,'usable_baselines':base,'conditional_controls':conditional,'retained_initial_failures':16,'blocked_baseline_records':2,'blocked_candidates_not_run':2,'model_calls':0},indent=2))
