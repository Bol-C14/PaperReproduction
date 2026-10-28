"""Static evidence verification; does not run upstream code or external tools."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parent
manifest=json.loads((ROOT/'assets.json').read_text())
for item in manifest['local_source_evidence']:
 p=ROOT/'upstream'/pathlib.Path(item['file']).name
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],p
metrics=json.loads((ROOT/'results/metrics.json').read_text())
ledger=json.loads((ROOT/'results/resource_ledger.json').read_text())
structural=json.loads((ROOT/'results/structural_loading.json').read_text())
assert metrics['tests_passed']==7
assert metrics['abc_evaluations']==ledger['abc_calls']==0
assert not metrics['behavioral_reproduction'] and metrics['adp_results'] is None
assert structural['keys']==26 and structural['all_tensors_equal_to_supplied_checkpoint']
assert not structural['inference_performed']
assert ledger['elapsed_seconds']<ledger['setup_limit_seconds']
assert ledger['total_download_conservative_bound_bytes']<ledger['download_limit_bytes']
assert 'HTTP/1.1 403' in (ROOT/'logs/bert_config_headers.txt').read_text()
changes=subprocess.check_output(['git','diff','f85c69748506854273c5816d29646d6a70f5f468','--name-only'],cwd=ROOT.parent,text=True).splitlines()
assert all(p.startswith('p09_abc_rl/') for p in changes),changes
checkpoint=ROOT/'assets/nn_model.pt'
if checkpoint.exists():
 assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()=='d4747eeff16c7247acf8f1480a33f2239a1a51adaac78a0a6e915c5ba12164f5'
print('PASS: original-source hashes, unit/structural evidence, gate403, limits, no ABC claims, and paper-local changes')
