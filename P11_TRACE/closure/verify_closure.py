"""Independent saved-output audit. No optimization, and no training evaluator imports."""
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics

R=Path(__file__).resolve().parent
frozen=json.loads((R/'frozen_families.json').read_text())
assert frozen['protocol_sha256']==hashlib.sha256((R/'PROTOCOL.md').read_bytes()).hexdigest()
rows={r['id']:r for r in frozen['rows']}
parents=frozen['parents']
splits={s:{p['parent'] for p in parents if p['split']==s} for s in ['train','support','query']}
assert all(splits[a].isdisjoint(splits[b]) for a,b in itertools.combinations(splits,2))
assert len(rows)==640 and len(parents)==80
summary=json.loads((R/'summary.json').read_text())
assert len(summary)==48
journal=[json.loads(l) for l in (R/'training_steps.jsonl').read_text().splitlines()]
assert len(journal)==2400


def truth(op,b):
    if op=='INV':return 1-b[0]
    if op=='AND':return int(all(b))
    if op=='OR':return int(any(b))
    if op=='XOR':return int(b[0]!=b[1])
    if op=='XNOR':return int(b[0]==b[1])
    if op=='MUX':return b[1] if not b[0] else b[2]
    if op=='MAJ':return int(sum(b)>1)
    raise ValueError(op)


def independent_local(op,p):
    # Operator truth-table expectation, independent of training's polynomial phi.
    result=0.
    for bits in itertools.product([0,1],repeat=len(p)):
        weight=math.prod(v if b else 1-v for v,b in zip(p,bits))
        result+=weight*truth(op,bits)
    return result


max_recurrence_delta=0.;max_metric_delta=0.;files_checked=0
for result in summary:
    track=result['track'];seed=result['seed'];family=result['family'];arm=result['arm']
    prefix=f'{seed}_{arm}_{family}' if track=='scratch_pretrain' else f'{seed}_transfer_{track.removeprefix("transfer_")}_{family}'
    assert result['adaptation']['steps']==20
    for stage in ['no_adapt','adapt']:
        prediction=json.loads((R/'predictions'/f'{prefix}_{stage}.json').read_text())
        assert len(prediction)==48
        node_errors=[];output_errors=[];outside=0
        for saved in prediction:
            row=rows[saved['id']]
            assert row['family']==family and row['split']=='query'
            assert max(abs(x-y) for x,y in zip(saved['target'],row['target']))<1e-6
            if arm=='fsl':
                reconstructed=list(row['pi_probs'])
                for i,node in enumerate(row['nodes'][6:],6):
                    reconstructed.append(independent_local(node['op'],[reconstructed[j] for j in node['inputs']])+saved['raw'][i])
                delta=max(abs(x-y) for x,y in zip(reconstructed,saved['prediction']))
                max_recurrence_delta=max(max_recurrence_delta,delta)
                assert delta<1e-5
            else:
                independent=[1/(1+math.exp(-v)) for v in saved['raw']]
                assert max(abs(x-y) for x,y in zip(independent,saved['prediction']))<1e-6
            node_errors.extend(abs(a-b) for a,b in zip(saved['prediction'][6:],row['target'][6:]))
            output_errors.append(abs(saved['prediction'][-1]-row['target'][-1]))
            outside+=sum(p<0 or p>1 for p in saved['prediction'][6:])
        for metric,errors in [('node_mae',node_errors),('output_mae',output_errors)]:
            delta=abs(statistics.mean(errors)-result[stage][metric]);max_metric_delta=max(max_metric_delta,delta)
            assert delta<1e-6
        assert outside==result[stage]['outside_unit']
        files_checked+=1
report=dict(status='pass',prediction_files=files_checked,optimizer_updates=len(journal),
    max_independent_recurrence_delta=max_recurrence_delta,max_independent_metric_delta=max_metric_delta,
    parent_split_disjoint=True,protocol_hash_verified=True)
(R/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
