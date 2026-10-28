"""Recompute raw objective/CEC evidence without importing the model or ABC."""
import argparse
import hashlib
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
args = parser.parse_args()
out = args.output
hashes = json.loads((out/'evidence_hashes.json').read_text())
verified = 0
for name, expected in hashes.items():
    path = out/name
    if path.exists():
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
        verified += 1
    else:
        assert name.endswith('.aig'), ('Missing text evidence',name)
assert len(list(out.glob('abc_*.log')))==724
entries = [json.loads(s) for s in (out/'calls.jsonl').read_text().splitlines()]
starts = [e for e in entries if 'id' in e and e['status']=='started']
rows = json.loads((out/'results.json').read_text())
maps = [e for e in starts if e['kind']=='mapped_adp']
assert len(maps)==len(rows)==362
for row, entry in zip(rows,maps):
    text = re.sub(r'\x1b\[[0-9;]*m','',(out/f'abc_{entry["id"]:04d}.log').read_text())
    area = float(re.findall(r'Area\s*=\s*([0-9.eE+-]+)',text)[-1])
    delay = float(re.findall(r'Delay\s*=\s*([0-9.eE+-]+)',text)[-1])
    assert (area,delay,area*delay)==(row['area'],row['delay'],row['adp'])
    assert row['recipe']==entry['recipe']
    assert starts[entry['id']]['kind']=='cec'
    assert 'Networks are equivalent' in (out/f'abc_{entry["id"]+1:04d}.log').read_text()
for seed in [566,567,568]:
    full = [(r['recipe'],r['adp'],r['valid']) for r in rows if (r['circuit'],r['arm'],r['seed'])==('cavlc','adaptive_full',seed)]
    subset = [(r['recipe'],r['adp'],r['valid']) for r in rows if (r['circuit'],r['arm'],r['seed'])==('cavlc','adaptive_subset',seed)]
    assert full==subset and len(full)==12
traces = [e for e in entries if e['kind']=='mcts_inference']
assert len(traces)==360 and all(e['valid'] for e in traces)
source = Path(__file__).resolve().parent
protocol = json.loads((out/'PROTOCOL.json').read_text())
assert hashlib.sha256((source/'april_ablation.py').read_bytes()).hexdigest()==protocol['runner_sha256']
assert hashlib.sha256((source/'repaired/LogicSynthesisPolicy.py').read_bytes()).hexdigest()==protocol['amendment']['policy_sha256']
result = dict(text_hashes_verified=verified,native_logs_verified=724,raw_adp_recomputed=362,cec_text_pass=362,cavlc_full_subset_identical_recipes_and_adp_all_3_seeds=True,mcts_trace_rows=360,runner_and_policy_match_frozen_hashes=True)
(out/'independent_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
