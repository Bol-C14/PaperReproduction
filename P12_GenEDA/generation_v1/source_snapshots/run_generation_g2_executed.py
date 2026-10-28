"""G1: tiny scratch decoder, real GenEDA answer targets, controlled alignment.

This is a methodology reconstruction, never pretrained GenEDA. No model download.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import resource
import sys
import time

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
sys.path.insert(0, str(HERE.parent / 'validation'))
from check_assets import cached_blob

torch.set_num_threads(3)
torch.set_num_interop_threads(1)
PAD, BOS, EOS, GRAPH = 0, 1, 2, 3
D, MAX_ANSWER, MAX_PROMPT = 64, 512, 192
ARMS = ['raw_matched', 'normalized_matched', 'normalized_shuffled', 'zero_modality', 'text_sft']


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def prepare_data():
    raw = cached_blob('benchmark/task1/data/Task1_summary_GenEDA.json')
    graphs = json.loads(raw)
    mapping = json.loads((HERE.parent / 'validation/results/pairing_map.json').read_text())['task1']
    family = {'Rocket': ('Rocket', 'train'), 'b14': ('ITC99', 'validation'), 'b20_1': ('ITC99', 'validation'),
              'VexRiscvSmallest': ('VexRiscv', 'test'), 'VexRiscvThreeStages': ('VexRiscv', 'test'),
              'VexRiscvTwoStagesMD': ('VexRiscv', 'test')}
    records = {s: [] for s in ['train', 'validation', 'test']}
    exclusions, seen_features, seen_targets = [], set(), set()
    for split, cap in [('train', 64), ('validation', 16), ('test', 16)]:
        ordered = sorted(mapping, key=lambda row: sha('g1:' + str(row['id'])))
        for entry in ordered:
            group = entry['module_group_proxy']
            if group not in family or family[group][1] != split:
                continue
            if entry['pairing_status'] != 'unique_text_row':
                exclusions.append({'id': entry['id'], 'reason': 'ambiguous text pairing'})
                continue
            row = graphs[entry['row']]
            answer = row['conversations'][1]['value']
            target_hash = sha(' '.join(answer.split()))
            feature_hash = entry['feature_sha256_float32']
            if feature_hash in seen_features or target_hash in seen_targets:
                exclusions.append({'id': entry['id'], 'reason': 'duplicate feature or normalized target'})
                continue
            if len(records[split]) >= cap:
                continue
            original_prompt = row['conversations'][0]['value']
            assert original_prompt.count('<image>') == 1
            interface = original_prompt.split('This design', 1)[-1].replace('<image>', '').strip()
            prompt = 'Describe circuit purpose and behavior.\nThis design ' + interface
            records[split].append({'id': entry['id'], 'source_row': entry['row'], 'module': group,
                                   'family': family[group][0], 'prompt': prompt,
                                   'answer': answer, 'graph': row['graph'],
                                   'feature_hash': feature_hash, 'label_hash': sha(answer),
                                   'normalized_target_hash': target_hash})
            seen_features.add(feature_hash)
            seen_targets.add(target_hash)
    # Explicit ancestry and exact duplicate assertions before model access.
    for a, b in [('train', 'validation'), ('train', 'test'), ('validation', 'test')]:
        for field in ['family', 'feature_hash', 'normalized_target_hash']:
            assert not {r[field] for r in records[a]} & {r[field] for r in records[b]}
    manifest = {'source_commit': '0a19fde3f1c1e56f49a367bf5f1914de84e1c951',
                'source_blob_sha256': hashlib.sha256(raw).hexdigest(),
                'protocol': 'G1', 'explicit_parent_ids_verified': False,
                'family_policy': family, 'excluded_unknown_family': 'Core',
                'records': {s: [{k: v for k, v in r.items() if k not in ['graph', 'answer']} for r in rows] for s, rows in records.items()},
                'exclusions': exclusions,
                'label_leakage_note': 'Training/validation/test exact normalized answers disjoint; ancestor relationship beyond declared project families and encoder pretraining exposure unverified.'}
    path = RESULTS / 'split_manifest.json'
    if path.exists():
        assert json.loads(path.read_text()) == json.loads(json.dumps(manifest)), 'Existing frozen manifest changed'
    else:
        write_json(path, manifest)
    return records


def byte_ids(text, limit):
    return [b + 4 for b in text.encode('utf-8')[:limit]]


def batch(rows, indices, language_only=False):
    xs, ys, fs = [], [], []
    for i in indices:
        row = rows[int(i)]
        answer = byte_ids(row['answer'], MAX_ANSWER) + [EOS]
        prefix = [BOS] if language_only else [BOS] + byte_ids(row['prompt'], MAX_PROMPT) + [GRAPH]
        sequence = prefix + answer
        x, y = sequence[:-1], sequence[1:]
        y[:len(prefix) - 1] = [-100] * (len(prefix) - 1)
        xs.append(x); ys.append(y); fs.append(row['graph'])
    length = max(map(len, xs))
    inputs = torch.tensor([x + [PAD] * (length - len(x)) for x in xs])
    labels = torch.tensor([y + [-100] * (length - len(y)) for y in ys])
    return inputs, labels, torch.tensor(fs, dtype=torch.float32)


class LoRALinear(nn.Module):
    def __init__(self, nin, nout):
        super().__init__()
        self.base = nn.Linear(nin, nout)
        self.a = nn.Parameter(torch.randn(4, nin) * 0.02)
        self.b = nn.Parameter(torch.zeros(nout, 4))
        self.enabled = False

    def forward(self, x):
        y = self.base(x)
        return y + F.linear(F.linear(x, self.a), self.b) if self.enabled else y


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.norm1, self.norm2 = nn.LayerNorm(D), nn.LayerNorm(D)
        self.qkv, self.proj = LoRALinear(D, 3 * D), LoRALinear(D, D)
        self.fc1, self.fc2 = LoRALinear(D, 2 * D), LoRALinear(2 * D, D)

    def forward(self, x, past=None):
        b, t, _ = x.shape
        q, k, v = self.qkv(self.norm1(x)).chunk(3, dim=-1)
        q, k, v = [a.reshape(b, t, 4, D // 4).transpose(1, 2) for a in [q, k, v]]
        if past is not None:
            k, v = torch.cat([past[0], k], dim=2), torch.cat([past[1], v], dim=2)
        z = F.scaled_dot_product_attention(q, k, v, is_causal=past is None and t > 1)
        x = x + self.proj(z.transpose(1, 2).reshape(b, t, D))
        x = x + self.fc2(F.gelu(self.fc1(self.norm2(x))))
        return x, (k, v)


class Decoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.tokens, self.positions = nn.Embedding(260, D), nn.Embedding(768, D)
        self.blocks = nn.ModuleList([Block(), Block()])
        self.norm = nn.LayerNorm(D)

    def forward(self, ids, graph_token=None, cache=None):
        offset = cache[0][0].shape[2] if cache is not None else 0
        h = self.tokens(ids)
        if graph_token is not None:
            h = torch.where((ids == GRAPH).unsqueeze(-1), graph_token.unsqueeze(1), h)
        h = h + self.positions(torch.arange(offset, offset + ids.shape[1]))
        caches = []
        for i, block in enumerate(self.blocks):
            h, state = block(h, None if cache is None else cache[i])
            caches.append(state)
        return F.linear(self.norm(h), self.tokens.weight), caches

    def setup(self, mode):
        for parameter in self.parameters():
            parameter.requires_grad_(mode == 'base')
        for module in self.modules():
            if isinstance(module, LoRALinear):
                module.enabled = mode == 'lora'
                module.a.requires_grad_(mode == 'lora')
                module.b.requires_grad_(mode == 'lora')


class Aligned(nn.Module):
    def __init__(self, base, mean, scale, arm):
        super().__init__()
        self.decoder = base
        self.connector = nn.Sequential(nn.Linear(768, D), nn.GELU(), nn.Linear(D, D))
        self.register_buffer('mean', mean)
        self.register_buffer('scale', scale)
        self.arm = arm

    def graph_token(self, graphs, intervention=None):
        if self.arm == 'text_sft' or intervention == 'remove':
            return torch.zeros((len(graphs), D))
        if self.arm == 'zero_modality':
            graphs = torch.zeros_like(graphs)
        elif self.arm != 'raw_matched':
            graphs = (graphs - self.mean) / self.scale
        return self.connector(graphs)

    def forward(self, ids, graphs, intervention=None, cache=None):
        return self.decoder(ids, self.graph_token(graphs, intervention), cache)


def loss(logits, labels):
    return F.cross_entropy(logits.reshape(-1, 260), labels.reshape(-1), ignore_index=-100)


def save_npz(path, model):
    np.savez_compressed(path, **{name: tensor.detach().numpy() for name, tensor in model.state_dict().items()})


def greedy(model, row, graph=None, intervention=None):
    ids = torch.tensor([[BOS] + byte_ids(row['prompt'], MAX_PROMPT) + [GRAPH]])
    g = torch.tensor([row['graph'] if graph is None else graph], dtype=torch.float32)
    output, cache = [], None
    with torch.no_grad():
        logits, cache = model(ids, g, intervention)
        for _ in range(MAX_ANSWER):
            token = int(logits[0, -1].argmax())
            if token == EOS:
                break
            output.append(token)
            logits, cache = model(torch.tensor([[token]]), g, intervention, cache)
    return bytes(t - 4 for t in output if 4 <= t < 260).decode('utf-8', errors='replace'), output


def main():
    global RESULTS
    parser = argparse.ArgumentParser()
    parser.add_argument('--pilot', action='store_true')
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--results-dir', default='results')
    parser.add_argument('--pretrain-steps', type=int, default=160)
    parser.add_argument('--stage1-steps', type=int, default=40)
    parser.add_argument('--stage2-steps', type=int, default=80)
    args = parser.parse_args()
    RESULTS = HERE / args.results_dir
    RESULTS.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    rows = prepare_data()
    seed = args.seed
    torch.manual_seed(seed)
    base = Decoder()
    base.setup('base')
    optimizer = torch.optim.AdamW([p for p in base.parameters() if p.requires_grad], lr=0.002)
    rng = np.random.default_rng(seed + 100)
    pretrain_batches = rng.integers(0, len(rows['train']), size=(args.pretrain_steps, 4)).tolist()
    trace = []
    nsteps = 10 if args.pilot else args.pretrain_steps
    for step, indices in enumerate(pretrain_batches[:nsteps]):
        inputs, labels, _ = batch(rows['train'], indices, language_only=True)
        value = loss(base(inputs)[0], labels)
        optimizer.zero_grad(); value.backward()
        nn.utils.clip_grad_norm_(base.parameters(), 1)
        optimizer.step()
        trace.append({'phase': 'scratch_language_pretrain', 'step': step, 'nll': value.item()})
        if step > 0 and step % 200 == 0:
            print('pretraining', seed, step, value.item(), flush=True)
    if args.pilot:
        elapsed = time.monotonic() - began
        write_json(RESULTS / 'pilot.json', {'seed': seed, 'steps': nsteps, 'elapsed_seconds': elapsed,
                   'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   'projected_training_seconds_1520_steps': elapsed / 10 * 1520,
                   'training_trace': trace, 'not_a_quality_selection_run': True})
        print('pilot', elapsed, 'seconds', flush=True)
        return
    initial = {k: v.detach().clone() for k, v in base.state_dict().items()}
    save_npz(RESULTS / f'base_seed{seed}.npz', base)
    graphs = torch.tensor([r['graph'] for r in rows['train']], dtype=torch.float32)
    mean, scale = graphs.mean(dim=0), graphs.std(dim=0).clamp_min(1e-8)
    task_steps = args.stage1_steps + args.stage2_steps
    batches = np.random.default_rng(seed).integers(0, len(rows['train']), size=(task_steps, 4)).tolist()
    order = np.random.default_rng(seed + 1).permutation(len(rows['train']))
    permutation = np.empty(len(order), dtype=np.int64)
    permutation[order] = np.roll(order, 1)
    assert np.all(permutation != np.arange(len(order)))
    write_json(RESULTS / f'budgets_seed{seed}.json', {'task_batch_ids': [[rows['train'][i]['id'] for i in indices] for indices in batches],
               'pretraining_batch_ids': [[rows['train'][i]['id'] for i in indices] for indices in pretrain_batches],
               'shuffle_mapping_ids': {str(rows['train'][i]['id']): rows['train'][int(permutation[i])]['id'] for i in range(len(permutation))}})
    write_json(RESULTS / f'pretrain_seed{seed}.json', trace)
    for arm in ARMS:
        arm_started = time.monotonic()
        torch.manual_seed(seed + 7)
        decoder = Decoder(); decoder.load_state_dict(initial)
        model = Aligned(decoder, mean, scale, arm)
        stage_metrics, stage_trace = [], []
        for phase, start, stop in [('connector_alignment', 0, args.stage1_steps), ('joint_adapter_alignment', args.stage1_steps, task_steps)]:
            decoder.setup('lora' if phase == 'joint_adapter_alignment' or arm == 'text_sft' else 'frozen')
            for p in model.connector.parameters():
                p.requires_grad_(arm != 'text_sft')
            parameters = [p for p in model.parameters() if p.requires_grad]
            optimizer = torch.optim.AdamW(parameters, lr=0.003)
            stage_metrics.append({'phase': phase, 'trainable_parameters': sum(p.numel() for p in parameters), 'steps': stop - start})
            for step in range(start, stop):
                indices = batches[step]
                inputs, labels, features = batch(rows['train'], indices)
                if arm == 'normalized_shuffled':
                    features = graphs[permutation[indices]]
                value = loss(model(inputs, features)[0], labels)
                optimizer.zero_grad(); value.backward()
                nn.utils.clip_grad_norm_(parameters, 1)
                optimizer.step()
                stage_trace.append({'phase': phase, 'step': step, 'nll': value.item()})
        print('trained', seed, arm, time.monotonic() - arm_started, flush=True)
        save_npz(RESULTS / f'model_{seed}_{arm}.npz', model)
        model.eval()
        generations = []
        for split in ['test', 'train']:
            examples = rows[split] if split == 'test' else rows[split][:4]
            for index, row in enumerate(examples):
                text, tokens = greedy(model, row)
                example = {'seed': seed, 'arm': arm, 'split': split, 'id': row['id'], 'family': row['family'],
                           'reference_prefix': row['answer'].encode('utf-8')[:MAX_ANSWER].decode('utf-8', errors='replace'),
                           'generated': text, 'generated_tokens': tokens, 'intervention': 'none'}
                generations.append(example)
                if split == 'test' and arm in ['raw_matched', 'normalized_matched']:
                    for intervention in ['remove', 'shuffle']:
                        other = examples[(index + 1) % len(examples)]['graph'] if intervention == 'shuffle' else None
                        changed, changed_tokens = greedy(model, row, other, intervention)
                        generations.append({**example, 'generated': changed, 'generated_tokens': changed_tokens, 'intervention': intervention})
        nll = []
        with torch.no_grad():
            for row in rows['test']:
                inputs, labels, features = batch([row], [0])
                nll.append({'id': row['id'], 'token_nll': loss(model(inputs, features)[0], labels).item()})
        record = {'method': 'scratch_decoder_methodology_reconstruction', 'seed': seed, 'arm': arm,
                  'stage_budgets': stage_metrics, 'task_trace': stage_trace, 'test_teacher_forced_nll': nll,
                  'wall_seconds_including_generation': time.monotonic() - arm_started,
                  'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'generations': generations}
        write_json(RESULTS / f'run_{seed}_{arm}.json', record)
        print('completed', seed, arm, len(generations), 'generations', flush=True)
    # Baselines are fixed from training answers; never use a held-out reference.
    counts = {}
    for row in rows['train']:
        answer = row['answer'][:MAX_ANSWER]
        counts[answer] = counts.get(answer, 0) + 1
    frequent = sorted(counts, key=lambda answer: (-counts[answer], sha(answer)))[0]
    baselines = []
    for row in rows['test']:
        for arm, text in [('generic_template', '(1) Interface: input and output signals. (2) Purpose: process input data. (3) Functionality: update outputs. (4) Constraints: clock and reset.'), ('training_answer_frequency', frequent)]:
            baselines.append({'seed': seed, 'arm': arm, 'split': 'test', 'id': row['id'], 'family': row['family'],
                              'reference_prefix': row['answer'].encode()[:MAX_ANSWER].decode(errors='replace'),
                              'generated': text, 'intervention': 'none'})
    write_json(RESULTS / f'baselines_seed{seed}.json', baselines)
    write_json(RESULTS / f'resources_seed{seed}.json', {'seed': seed, 'wall_seconds': time.monotonic() - began,
               'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'torch_threads': torch.get_num_threads(), 'base_model_parameters': sum(p.numel() for p in base.parameters()),
               'new_network_download_bytes': 0, 'decoder_pretraining_steps': args.pretrain_steps,
               'arms_completed': ARMS, 'task_steps_per_arm': task_steps,
               'stage1_steps': args.stage1_steps, 'stage2_steps': args.stage2_steps})


if __name__ == '__main__':
    main()
