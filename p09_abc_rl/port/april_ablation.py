"""Counted CPU ablation, GPL-3.0 (uses preserved GPL upstream modules).

Freeze PROTOCOL before execution. Never reuse a completed output directory.
No network access in this runner; public asset preparation is separate.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    protocol = json.loads(args.protocol.read_text())
    assert digest(__file__) == protocol['runner_sha256']
    assert os.environ['HF_HUB_OFFLINE'] == '1'
    assert os.environ['TRANSFORMERS_OFFLINE'] == '1'
    assert set(os.sched_getaffinity(0)) <= set(range(8))
    out = root / 'results/abc-rl' / protocol['run_id']
    out.mkdir(exist_ok=False)
    (out / 'PROTOCOL.json').write_bytes(args.protocol.read_bytes())
    source = Path(__file__).resolve().parent
    sys.path[:0] = [str(source / 'repaired'), str(source)]
    import numpy as np
    import torch
    import abc_py
    from trainer import Trainer
    from LogicSynthesisEnv import LogicSynthesisEnv, RESYN2_CMD, synthesisOpToPosDic
    from mcts import MCTSNode
    from mechanism import nearest_distance, guidance_exponent

    threads = min(8, len(os.sched_getaffinity(0)))
    torch.set_num_threads(threads)
    torch.manual_seed(566)
    assets = root / 'assets/abc-rl'
    abc = root / 'tools/abc-rl/abc/abc'
    ledger = out / 'calls.jsonl'
    calls = 0
    rows = []
    started = time.monotonic()

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2) + '\n')

    def record(value):
        with ledger.open('a') as stream:
            stream.write(json.dumps(value) + '\n')
            stream.flush()

    def native(kind, command, meta):
        nonlocal calls
        calls += 1
        assert calls <= protocol['budget']['hard_cap']
        entry = dict(id=calls, kind=kind, command=[str(abc), '-c', command], **meta)
        record(dict(**entry, status='started'))
        tick = time.monotonic()
        try:
            cp = subprocess.run(entry['command'], capture_output=True, text=True, timeout=120)
            text = cp.stdout + cp.stderr
            (out / f'abc_{calls:04d}.log').write_text(text)
            record(dict(**entry, status='finished', returncode=cp.returncode, seconds=time.monotonic()-tick))
            return cp.returncode, re.sub(r'\x1b\[[0-9;]*m', '', text)
        except subprocess.TimeoutExpired as exc:
            text = str(exc.stdout or '') + str(exc.stderr or '')
            (out / f'abc_{calls:04d}.log').write_text(text)
            record(dict(**entry, status='failed', error='timeout', seconds=time.monotonic()-tick))
            return -1, text

    # Every graph is a real source AIG; training list is frozen from source split5001.
    bank_names = protocol['source_train_bank']
    eval_names = protocol['circuits']
    assert not set(bank_names) & set(eval_names)
    file_names = [n+'.aig' for n in bank_names+eval_names] + ['nn_model.pt', '7nm.lib']
    save('asset_hashes.json', {n: digest(assets/n) for n in file_names})
    trainer = Trainer(str(assets / 'nn_model.pt'))
    trainer.step_model.eval()
    state = torch.load(assets/'nn_model.pt', weights_only=True, map_location='cpu')
    assert len(state) == 26
    assert all(torch.equal(v, trainer.step_model.state_dict()[k]) for k, v in state.items())
    env = LogicSynthesisEnv.__new__(LogicSynthesisEnv)
    graphs, inference = {}, {}
    for name in bank_names + eval_names:
        tick = time.monotonic()
        record(dict(kind='native_graph_read', circuit=name, status='started'))
        env._abc = abc_py.AbcInterface()
        env._abc.start()
        try:
            graph = env.extract_init_graph(str(assets / (name+'.aig')))
        finally:
            env._abc.end()
        assert int(graph['edge_index'].max()) < graph['nodes']
        data = env.createDataFromGraphAndSequence('0 0', graph)
        pi, val, emb = trainer.stepNgetEmbedding([data])
        assert np.isfinite(pi).all() and np.isfinite(emb).all()
        inference[name] = dict(nodes=graph['nodes'], edges=graph['edge_index'].shape[1], embedding=emb[0].tolist(), policy=pi[0].tolist(), seconds=time.monotonic()-tick)
        if name in eval_names:
            graphs[name] = graph
        record(dict(kind='native_graph_read', circuit=name, status='finished', seconds=time.monotonic()-tick))
    gates = {}
    for name in eval_names:
        gates[name] = {}
        for label, names in [('full', bank_names), ('subset', ['alu2', 'int2float'])]:
            distances = {n: nearest_distance(inference[name]['embedding'], [inference[n]['embedding']]) for n in names}
            nearest = min(distances, key=distances.get)
            distance = distances[nearest]
            gates[name][label] = dict(distance=distance, nearest=nearest, beta=guidance_exponent(distance), distances=distances)
    save('inference.json', dict(strict_keys=len(state), circuits=inference, gates=gates, retrieval_seconds=time.monotonic()-started))

    def evaluate(name, recipe, arm, seed, iteration):
        meta = dict(circuit=name, arm=arm, seed=seed, iteration=iteration)
        path = out / f'{name}_{arm}_{seed}_{iteration}.aig'
        command = f'read {assets/(name+".aig")}; {recipe}; write {path}; read_lib {assets/"7nm.lib"}; map; topo; stime'
        rc, text = native('mapped_adp', command, dict(**meta, recipe=recipe))
        area = re.findall(r'Area\s*=\s*([0-9.eE+-]+)', text)
        delay = re.findall(r'Delay\s*=\s*([0-9.eE+-]+)', text)
        row = dict(**meta, recipe=recipe, path=str(path), map_returncode=rc, valid=False)
        if rc == 0 and area and delay and path.exists():
            a, d = float(area[-1]), float(delay[-1])
            if np.isfinite(a*d) and a > 0 and d > 0:
                row.update(area=a, delay=d, adp=a*d)
        # Certify every generated candidate, including baselines and losers.
        if path.exists():
            cec_rc, cec_text = native('cec', f'cec {assets/(name+".aig")} {path}', meta)
            row['cec_returncode'] = cec_rc
            row['cec_equivalent'] = cec_rc == 0 and 'Networks are equivalent' in cec_text
            row['valid'] = 'adp' in row and row['cec_equivalent']
        rows.append(row)
        save('results.json', rows)
        return row

    class LazyEnv:
        n_actions = 7

        def next_state(self, state, depth, action):
            assert depth < 10
            return state + str(int(action))

        def is_done_state(self, depth):
            return depth == 10

    for name in eval_names:
        baseline = evaluate(name, RESYN2_CMD, 'resyn2', -1, 0)
        assert baseline['valid'], 'Invalid baseline; stop without tuning or replacement'
        for seed in protocol['seeds']:
            # Rotate execution order to limit systematic arm/time confounding.
            arms = protocol['arms']
            offset = protocol['seeds'].index(seed) % len(arms)
            for arm in arms[offset:] + arms[:offset]:
                # Separate shared suffix and starting-action streams avoid draw-count confounding.
                rng = np.random.default_rng(seed)
                start_rng = np.random.default_rng(seed+100000)
                beta = {'unguided': 0., 'policy_start': 0., 'fixed': 1., 'adaptive_full': gates[name]['full']['beta'], 'adaptive_subset': gates[name]['subset']['beta']}[arm]
                tree = MCTSNode('', '', 7, LazyEnv(), graphData=graphs[name])
                best = float('inf')
                for iteration in range(protocol['recipes_per_arm']):
                    leaf = tree.select_leaf()
                    prefix = tuple(map(int, leaf.state))
                    # Draw a full horizon vector for all arms, even if prefix lengths differ.
                    suffix = tuple(int(x) for x in rng.integers(0, 7, size=10))
                    random_start = int(start_rng.integers(7))
                    if len(prefix) < 10:
                        sentence = str(len(prefix)) + ' ' + ' '.join('0'+''.join(map(str, prefix)))
                        data = env.createDataFromGraphAndSequence(sentence, graphs[name])
                        pi, _, _ = trainer.stepNgetEmbedding([data])
                        assert np.isfinite(pi).all() and (pi > 0).all()
                        priors = np.power(pi[0], beta)
                        first = random_start if arm == 'unguided' else int(np.argmax(pi[0]))
                        actions = prefix + (first,) + suffix[len(prefix)+1:]
                    else:
                        actions = prefix
                        pi = np.zeros((1, 7))
                        priors = np.ones(7)
                    assert len(actions) == 10
                    recipe = '; '.join(synthesisOpToPosDic[a] for a in actions)
                    row = evaluate(name, recipe, arm, seed, iteration)
                    reward = max(-1., 1.-row['adp']/baseline['adp']) if row['valid'] else -1.
                    if len(prefix) == 10:
                        leaf.backup_value(reward, reward, up_to=tree)
                    else:
                        leaf.incorporate_estimates(priors, reward, reward, up_to=tree)
                    if row['valid']:
                        best = min(best, row['adp'])
                    record(dict(kind='mcts_inference', circuit=name, seed=seed, arm=arm, iteration=iteration, prefix=list(prefix), actions=list(actions), beta=beta, policy=pi[0].tolist(), priors=priors.tolist(), reward=reward, valid=row['valid'], best_adp=best if np.isfinite(best) else None, root_visits=tree.child_N.tolist(), root_monte_carlo=tree.child_M.tolist()))
                print('ARM_COMPLETE', name, seed, arm, calls, flush=True)
    entries = [json.loads(line) for line in ledger.read_text().splitlines()]
    launches = [e for e in entries if e.get('id') and e['status'] == 'started']
    finishes = [e for e in entries if e.get('id') and e['status'] in ['finished', 'failed']]
    assert calls == protocol['budget']['planned_abc_calls']
    assert len(launches) == len(finishes) == calls
    save('audit.json', dict(calls=calls, mapped_adp=sum(e['kind']=='mapped_adp' for e in launches), cec=sum(e['kind']=='cec' for e in launches), native_graph_reads=len(inference), failures=[e for e in finishes if e.get('returncode', -1)!=0], invalid_rows=[r for r in rows if not r['valid']], seconds=time.monotonic()-started, affinity=sorted(os.sched_getaffinity(0)), threads=threads, protocol_sha256=digest(args.protocol), runner_sha256=digest(__file__)))
    print('ABLATION_COMPLETE', calls, flush=True)


if __name__ == '__main__':
    main()
