"""Independently audit complete saved evidence; no synthesis or model call."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
args = parser.parse_args()
out = args.output
protocol = json.loads((out/'PROTOCOL.json').read_text())
rows = json.loads((out/'results.json').read_text())
entries = [json.loads(s) for s in (out/'calls.jsonl').read_text().splitlines()]
starts = [e for e in entries if 'id' in e and e['status']=='started']
ends = [e for e in entries if 'id' in e and e['status'] in ('finished','failed')]
assert len(starts) == len(ends) == protocol['budget']['planned_abc_calls'] == 724
assert [e['id'] for e in starts] == list(range(1,725))
assert Counter(e['id'] for e in ends) == Counter(e['id'] for e in starts)
assert len(rows) == 362
assert len({(r['circuit'],r['arm'],r['seed'],r['iteration']) for r in rows}) == 362
assert Counter(e['kind'] for e in starts) == dict(mapped_adp=362, cec=362)
assert sum(e['kind']=='native_graph_read' and e['status']=='finished' for e in entries)==24
cec_logs = [(out/f'abc_{e["id"]:04d}.log').read_text() for e in starts if e['kind']=='cec']
cec_pass = sum('Networks are equivalent' in s for s in cec_logs)
summary, curves = {}, []
for circuit in protocol['circuits']:
    baseline = next(r['adp'] for r in rows if r['circuit']==circuit and r['arm']=='resyn2')
    arms = {}
    for arm in protocol['arms']:
        values = []
        for seed in protocol['seeds']:
            sample = sorted([r for r in rows if (r['circuit'],r['arm'],r['seed'])==(circuit,arm,seed)],key=lambda r:r['iteration'])
            assert [r['iteration'] for r in sample] == list(range(12))
            best = float('inf')
            for r in sample:
                assert len([s for s in r['recipe'].split(';') if s.strip()])==10
                if r['valid']:
                    best = min(best,r['adp'])
                curves.append(dict(circuit=circuit,arm=arm,seed=seed,recipe_calls=r['iteration']+1,abc_calls_including_cec=2*(r['iteration']+1),best_adp=best if best<float('inf') else None))
            valid = [r for r in sample if r['valid']]
            assert valid, 'Entire arm invalid; do not summarize as numerical winner'
            winner = min(valid,key=lambda r:r['adp'])
            values.append(dict(seed=seed,best_adp=winner['adp'],reduction_percent=100*(1-winner['adp']/baseline),winner_iteration=winner['iteration'],valid_candidates=len(valid)))
        reductions = [r['reduction_percent'] for r in values]
        arms[arm] = dict(seeds=values,median_reduction_percent=statistics.median(reductions),min_reduction_percent=min(reductions),max_reduction_percent=max(reductions))
    paired = {}
    for a,b in [('policy_start','unguided'),('fixed','policy_start'),('adaptive_full','fixed'),('adaptive_full','adaptive_subset')]:
        diffs = [dict(seed=x['seed'],reduction_difference_pp=x['reduction_percent']-y['reduction_percent']) for x,y in zip(arms[a]['seeds'],arms[b]['seeds'])]
        paired[a+' minus '+b] = dict(seeds=diffs,median_difference_pp=statistics.median(v['reduction_difference_pp'] for v in diffs))
    summary[circuit] = dict(baseline_adp=baseline,arms=arms,paired=paired)
failures = [e for e in ends if e.get('returncode',-1)!=0]
result = dict(abc_calls=724,mapped_adp=362,cec=362,cec_pass=cec_pass,failed_calls=failures,invalid_candidates=[r for r in rows if not r['valid']],circuits=summary)
(out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'curves.json').write_text(json.dumps(curves,indent=2)+'\n')
manifest = out/'evidence_hashes.json'
if manifest.exists():
    # Preserve the remote binary-AIG inventory when inspecting a text export.
    for name, expected in json.loads(manifest.read_text()).items():
        if (out/name).exists():
            assert hashlib.sha256((out/name).read_bytes()).hexdigest()==expected,name
else:
    hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name!='evidence_hashes.json'}
    manifest.write_text(json.dumps(hashes,indent=2)+'\n')
print(json.dumps(result,indent=2))
