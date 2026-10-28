"""Read-only verification of saved predictions, split membership and source hashes."""
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parent
rows = json.loads((root/'frozen_circuits.json').read_text())
assert rows['protocol_sha256'] == hashlib.sha256((root/'PROTOCOL.md').read_bytes()).hexdigest()
test = [r for r in rows['samples'] if r['split']=='test']
train = [r for r in rows['samples'] if r['split']=='train']
assert {r['parent'] for r in train}.isdisjoint({r['parent'] for r in test})
assert len(train)==64 and len(test)==32
records = [json.loads(line) for line in (root.parent/'RESULTS.jsonl').read_text().splitlines()]
for arm in ['direct','residual']:
 saved = json.loads((root/f'{arm}_predictions.json').read_text())
 target = [v for r in test for v in r['global_prob']]
 assert len(saved['target'])==len(target)==256
 assert max(abs(x-y) for x,y in zip(target,saved['target']))<1e-6
 non_pi=[i for i in range(len(target)) if i%8>=3]
 out=saved['outputs']
 observed=next(r for r in records if r['phase']=='learning_arm' and r['arm']==arm)
 for name,idx in [('non_pi_mae',non_pi),('output_mae',out)]:
  mae=sum(abs(saved['prediction'][i]-target[i]) for i in idx)/len(idx)
  assert abs(mae-observed['final_test'][name])<1e-6
 assert observed['optimizer_steps']==120 and observed['rename_max_abs']<=1e-6
versions=json.loads((root/'SOURCE_VERSIONS.json').read_text())
for src in versions['sources']:
 assert hashlib.sha256((root/src['vendored_path']).read_bytes()).hexdigest()==src['sha256']
print('PASS: protocol/data hashes, parent split, both saved MAEs/steps/rename controls, and seven upstream source hashes')
