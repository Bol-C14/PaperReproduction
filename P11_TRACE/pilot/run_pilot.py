"""Frozen, bounded CPU methodology pilot; see PROTOCOL.md before interpreting."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import resource
import sys
import time
import traceback
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT.parent / 'RESULTS.jsonl'
START = time.monotonic()


def record(phase, **data):
    entry = dict(phase=phase, utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                 elapsed_s=time.monotonic() - START, **data)
    with RESULTS.open('a') as f:
        f.write(json.dumps(entry, allow_nan=False) + '\n')
    print(json.dumps(entry), flush=True)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exact_labels(nodes, probs):
    """Independent PI Bernoulli joint, exact 2^3 enumeration, no simulation."""
    means = [0.] * len(nodes)
    for bits in itertools.product([0, 1], repeat=3):
        weight = 1.
        for p, b in zip(probs, bits):
            weight *= p if b else 1 - p
        values = list(bits)
        for gate, fanins in nodes[3:]:
            values.append(values[fanins[0]] & values[fanins[1]] if gate == 'AND'
                          else 1 - values[fanins[0]])
        for i, v in enumerate(values):
            means[i] += weight * v
    residual = [0.] * len(nodes)
    for i, (gate, fanins) in enumerate(nodes):
        if gate == 'AND':
            residual[i] = means[i] - means[fanins[0]] * means[fanins[1]]
    return means, residual


def freeze_data():
    rows = []
    parents = []
    grid = list(itertools.product([.2, .5, .8], repeat=3))
    for parent in range(100, 112):
        rng = random.Random(parent)
        nodes = [('PI', []) for _ in range(3)]
        for idx in range(3, 7):
            gate = rng.choice(['AND', 'AND', 'NOT'])
            nodes.append((gate, [rng.randrange(idx) for _ in range(2 if gate == 'AND' else 1)]))
        nodes.append(('AND', [6, nodes[6][1][0]]))
        topology = json.dumps(nodes)
        parents.append(dict(parent=parent, split='train' if parent < 108 else 'test',
                            topology_sha256=hashlib.sha256(topology.encode()).hexdigest(), nodes=nodes))
        for probs in random.Random(parent + 1000).sample(grid, 8):
            means, residual = exact_labels(nodes, probs)
            rows.append(dict(parent=parent, split=parents[-1]['split'], nodes=nodes,
                             pi_probs=probs, global_prob=means, residual=residual))
    train_hashes = {p['topology_sha256'] for p in parents if p['split'] == 'train'}
    test_hashes = {p['topology_sha256'] for p in parents if p['split'] == 'test'}
    assert not train_hashes & test_hashes
    data_path = ROOT / 'frozen_circuits.json'
    content = json.dumps(dict(protocol_sha256=digest(ROOT / 'PROTOCOL.md'), parents=parents,
                              samples=rows), indent=2) + '\n'
    if data_path.exists():
        assert data_path.read_text() == content, 'Frozen dataset differs; refusing overwrite'
    else:
        data_path.write_text(content)
    record('data_frozen', status='pass', sha256=digest(data_path), parents=12,
           train_samples=64, test_samples=32, train_test_topology_overlap=0)
    return rows


def main():
    import torch
    import torch_geometric
    from torch_geometric.data import Data
    from vendor.aig.trace_encoder_impl import TRACE
    from vendor.aig.mlp import MLP
    from vendor.aig.cov2prob import cov2prob
    sys.path.insert(0, str(ROOT / 'vendor/tutorial'))
    from expr_graphs import build_graph_template, add_sample_values
    from data import compute_expression
    from model import TRACEComputationalGraph
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.manual_seed(2026)
    record('imports', status='pass', torch=torch.__version__, pyg=torch_geometric.__version__,
           device='cpu', threads=torch.get_num_threads(), cuda_initialized=torch.cuda.is_initialized())
    assert compute_expression('sub', 3, 5, 97) == 95
    assert compute_expression('x2_xy_y2', 3, 5, 97) == 49
    tutorial = TRACEComputationalGraph(p=97, hidden=64, num_layers=1, num_heads=4).eval()
    demo = add_sample_values(build_graph_template('x2_xy_y2'), 3, 5)
    with torch.no_grad():
        pred, trace = tutorial(demo, return_trace=True)
    record('tutorial_forward', status='pass', trained=False, prediction=float(pred.item()),
           analytic_target=49/96, trace_levels=len(trace), claim='architecture walkthrough only')

    def tutorial_rename(g):
        # new_to_old reversed. Preserve valid levels, semantic PI types, and edge ports.
        new_to_old = torch.arange(g.num_nodes - 1, -1, -1)
        old_to_new = torch.argsort(new_to_old)
        h = g.clone()
        for key in ['node_type', 'node_value', 'forward_level']:
            h[key] = g[key][new_to_old]
        h.edge_index = old_to_new[g.edge_index]
        h.output_node_idx = old_to_new[g.output_node_idx]
        return h

    with torch.no_grad():
        renamed = tutorial(tutorial_rename(demo))
        shuffled = demo.clone()
        order = torch.arange(demo.edge_index.shape[1]-1, -1, -1)
        shuffled.edge_index = demo.edge_index[:, order]
        shuffled.edge_pos = demo.edge_pos[order]
        reordered = tutorial(shuffled)
        sub = add_sample_values(build_graph_template('sub'), 3, 5)
        swapped = sub.clone()
        incoming = (sub.edge_index[1] == 2).nonzero().view(-1)
        swapped.edge_pos[incoming] = swapped.edge_pos[incoming].flip(0)
        sub_delta = float((tutorial(sub) - tutorial(swapped)).abs().item())
    rename_delta = float((pred - renamed).abs().max())
    reorder_delta = float((pred - reordered).abs().max())
    assert rename_delta <= 1e-6 and reorder_delta <= 1e-6
    mux = lambda s, a, b: b if s else a
    assert mux(0, 1, 0) == 1 and mux(1, 0, 0) == 0
    assert compute_expression('sub', 5, 3, 97) == 2
    assert compute_expression('add', 3, 5, 97) == compute_expression('add', 5, 3, 97)
    record('role_controls', status='pass', tutorial_rename_max_abs=rename_delta,
           tutorial_edge_reorder_max_abs=reorder_delta, untrained_sub_output_delta=sub_delta,
           sub_exact_targets=[95, 2], mux_exact_targets=[1, 0], mux_learned=False,
           add_swap_exact_invariant=True, limitation='SUB response is untrained structural sensitivity')

    def graph(row):
        nodes = row['nodes']
        edges, levels = [], [0] * len(nodes)
        for i, (_, fanins) in enumerate(nodes):
            for j in fanins:
                edges.append([j, i])
            if fanins:
                levels[i] = 1 + max(levels[j] for j in fanins)
        return Data(gate=torch.tensor([dict(PI=0, AND=1, NOT=2)[n[0]] for n in nodes]),
                    edge_index=torch.tensor(edges, dtype=torch.long).t().contiguous(),
                    forward_level=torch.tensor(levels), forward_index=torch.arange(len(nodes)),
                    prob=torch.tensor(row['global_prob'], dtype=torch.float32),
                    cov=torch.tensor(row['residual'], dtype=torch.float32),
                    num_nodes=len(nodes))

    # Do not use PyG collation's default forward_index increment behavior.
    def merge(rows):
        gs = [graph(r) for r in rows]
        n = gs[0].num_nodes
        return Data(gate=torch.cat([g.gate for g in gs]),
                    edge_index=torch.cat([g.edge_index + i*n for i, g in enumerate(gs)], dim=1),
                    forward_level=torch.cat([g.forward_level for g in gs]),
                    forward_index=torch.arange(n*len(gs)),
                    prob=torch.cat([g.prob for g in gs]), cov=torch.cat([g.cov for g in gs]),
                    num_nodes=n*len(gs))

    rows = freeze_data()
    for diagnostic, nodes, expected, expected_residual in [
        ('contradiction', [('PI', [])]*3 + [('NOT', [0]), ('AND', [0, 3])], 0., -.25),
        ('independent', [('PI', [])]*3 + [('AND', [0, 1])], .25, 0.)]:
        means, cov = exact_labels(nodes, [.5]*3)
        assert abs(means[-1]-expected) < 1e-12 and abs(cov[-1]-expected_residual) < 1e-12
        record('label_diagnostic', name=diagnostic, status='pass', exact=means[-1], residual=cov[-1])
    oracle_error = 0.
    for r in rows:
        g = graph(r)
        oracle_error = max(oracle_error, float((cov2prob(g, g.cov)-g.prob).abs().max()))
    assert oracle_error <= 1e-6
    record('oracle_reconstruction', status='pass', max_abs_error=oracle_error)
    train_rows = [r for r in rows if r['split'] == 'train']
    test_rows = [r for r in rows if r['split'] == 'test']
    train, test = merge(train_rows), merge(test_rows)
    output_test = torch.arange(7, test.num_nodes, 8)

    def metrics(g, probability, outputs):
        mask = g.forward_level > 0
        return dict(non_pi_mae=float((probability[mask]-g.prob[mask]).abs().mean()),
                    output_mae=float((probability[outputs]-g.prob[outputs]).abs().mean()),
                    outside_unit_interval=int(((probability < 0) | (probability > 1)).sum()),
                    min_prediction=float(probability.min()), max_prediction=float(probability.max()))

    local = cov2prob(test, torch.zeros_like(test.prob))
    record('local_baseline', split='test', status='pass', **metrics(test, local, output_test))

    class Pilot(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = TRACE(SimpleNamespace(), num_rounds=1, dim_hidden=32)
            self.head = MLP(32, 16, 1, num_layer=3)

        def forward(self, g):
            return self.head(self.encoder(g)).squeeze(-1)

    for arm in ['direct', 'residual']:
        arm_start = time.monotonic()
        try:
            torch.manual_seed(2026)
            model = Pilot()
            optimizer = torch.optim.Adam(model.parameters(), lr=.001)
            params = sum(p.numel() for p in model.parameters())
            steps = []
            def probability(g):
                raw = model(g)
                return raw.clamp(0, 1) if arm == 'direct' else cov2prob(g, raw.clamp(-1, 1))
            model.eval()
            with torch.no_grad():
                initial = metrics(test, probability(test), output_test)
            model.train()
            mask = train.forward_level > 0 if arm == 'direct' else train.gate == 1
            target = train.prob if arm == 'direct' else train.cov
            for step in range(120):
                if time.monotonic() - arm_start > 600:
                    raise TimeoutError('Frozen 600-second arm limit exceeded')
                optimizer.zero_grad()
                raw = model(train)
                prediction = raw.clamp(0, 1) if arm == 'direct' else raw.clamp(-1, 1)
                loss = torch.nn.functional.l1_loss(prediction[mask], target[mask])
                assert torch.isfinite(loss)
                loss.backward()
                optimizer.step()
                if step in [0, 29, 59, 89, 119]:
                    steps.append(dict(step=step+1, training_l1=float(loss.detach())))
            model.eval()
            with torch.no_grad():
                final_probability = probability(test)
                final = metrics(test, final_probability, output_test)
                tr = metrics(train, probability(train), torch.arange(7, train.num_nodes, 8))
                # Rename each of 32 graphs; retain edge grouping and semantic input distribution.
                renamed_g = test.clone()
                new_to_old = torch.arange(test.num_nodes).reshape(-1, 8).flip(1).reshape(-1)
                old_to_new = torch.argsort(new_to_old)
                for key in ['gate', 'forward_level', 'prob', 'cov']:
                    renamed_g[key] = test[key][new_to_old]
                renamed_g.edge_index = old_to_new[test.edge_index]
                renamed_g.forward_index = torch.arange(test.num_nodes)
                renamed_probability = probability(renamed_g)[old_to_new]
                rename_error = float((final_probability-renamed_probability).abs().max())
                assert rename_error <= 1e-6
            torch.save(model.state_dict(), ROOT / f'{arm}_pilot_weights.pt')
            (ROOT / f'{arm}_predictions.json').write_text(json.dumps(dict(
                target=test.prob.tolist(), prediction=final_probability.tolist(),
                outputs=output_test.tolist()), indent=2)+'\n')
            record('learning_arm', arm=arm, status='pass', seed=2026, optimizer_steps=120,
                   params=params, seconds=time.monotonic()-arm_start, training_history=steps,
                   initial_test=initial, final_test=final, final_train=tr,
                   rename_max_abs=rename_error, model='official AIG TRACE hidden32 rounds1 + official MLP')
        except Exception as exc:
            record('learning_arm', arm=arm, status='failed', seconds=time.monotonic()-arm_start,
                   error=repr(exc), traceback=traceback.format_exc())
    record('complete', status='finished', wall_seconds=time.monotonic()-START,
           process_cpu_seconds=time.process_time(), peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           cuda_initialized=torch.cuda.is_initialized())


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        record('fatal', status='failed', error=repr(exc), traceback=traceback.format_exc())
        raise
