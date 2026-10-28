"""Inspect cached official JSON assets and freeze an explicitly educational split."""
from __future__ import annotations

import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / 'P12_GenEDA_source'
COMMIT = '0a19fde3f1c1e56f49a367bf5f1914de84e1c951'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_hash(text: str) -> str:
    return digest(text.encode('utf-8'))


def cached_blob(path: str) -> bytes:
    # Never lazily fetch missing objects while examining existing assets.
    oid = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', COMMIT + ':' + path], text=True).strip()
    return subprocess.check_output(['git', '-C', str(SOURCE), 'cat-file', 'blob', oid], env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'})


def inspect_task(task: int):
    name = 'summary' if task == 1 else 'implementation'
    prefix = f'benchmark/task{task}/data/Task{task}_{name}'
    raw_text, raw_graph = cached_blob(prefix + '.json'), cached_blob(prefix + '_GenEDA.json')
    text, graph = json.loads(raw_text), json.loads(raw_graph)
    targets = collections.defaultdict(list)
    for index, row in enumerate(text):
        modules = re.findall(r'\bmodule\s+(\S+)\s*\(', row['input'])
        targets[text_hash(row['label'])].append({'text_row': index, 'module': modules[0] if modules else None})
    rows, problems = [], []
    for index, row in enumerate(graph):
        turns = row.get('conversations', [])
        good_turns = len(turns) == 2 and turns[0].get('from') == 'human' and turns[1].get('from') == 'gpt'
        vector = np.asarray(row.get('graph', []), dtype=np.float32)
        label = turns[1]['value'] if good_turns else ''
        prompt = turns[0]['value'] if good_turns else ''
        candidates = targets.get(text_hash(label), [])
        groups = sorted({x['module'] for x in candidates if x['module'] is not None})
        group = groups[0] if len(groups) == 1 and all(x['module'] is not None for x in candidates) else None
        entry = {'row': index, 'id': row.get('id'), 'shape': list(vector.shape),
                 'finite': bool(np.isfinite(vector).all()), 'turns_valid': good_turns,
                 'image_markers': prompt.count('<image>'),
                 'feature_sha256_float32': digest(vector.astype('<f4').tobytes()),
                 'label_sha256': text_hash(label), 'exact_label_text_matches': candidates,
                 'module_group_proxy': group,
                 'pairing_status': 'unique_text_row' if len(candidates) == 1 else 'ambiguous_rows_same_module' if group else 'ambiguous_or_unmatched'}
        if vector.shape != (768,) or not entry['finite'] or not good_turns or entry['image_markers'] != 1:
            problems.append(row.get('id'))
        rows.append(entry)
    ids = [row['id'] for row in rows]
    feature_counts = collections.Counter(row['feature_sha256_float32'] for row in rows)
    groups = collections.Counter(row['module_group_proxy'] for row in rows)
    metrics = {
        'task': task, 'text_records': len(text), 'graph_records': len(graph),
        'text_blob_sha256': digest(raw_text), 'graph_blob_sha256': digest(raw_graph),
        'unique_ids': len(set(ids)), 'ids_equal_row_index': ids == list(range(len(ids))),
        'all_vectors_768_finite_valid_turns_one_marker': not problems, 'invalid_record_ids': problems,
        'exact_label_join_unique_rows': sum(x['pairing_status'] == 'unique_text_row' for x in rows),
        'exact_label_join_ambiguous_same_module': sum(x['pairing_status'] == 'ambiguous_rows_same_module' for x in rows),
        'unmatched_or_ambiguous_group': sum(x['module_group_proxy'] is None for x in rows),
        'module_group_proxy_counts': {str(k): v for k, v in sorted(groups.items(), key=lambda item: str(item[0]))},
        'unique_feature_vectors_float32': len(feature_counts),
        'duplicate_feature_buckets': sum(c > 1 for c in feature_counts.values()),
        'duplicate_feature_extra_rows': sum(c - 1 for c in feature_counts.values()),
        'parent_design_ids_explicitly_present': False,
        'parent_group_caveat': 'Exact reference-label joins recover module names, not independently verified project/parent IDs. Same target text need not establish unique physical-circuit pairing.'}
    return metrics, rows, graph


def main():
    start = time.monotonic()
    (HERE / 'results').mkdir(exist_ok=True)
    tasks = [inspect_task(task) for task in (1, 2)]
    by_id = [{row['id']: row for row in rows} for _, rows, _ in tasks]
    common = sorted(set(by_id[0]) & set(by_id[1]))
    cross = {
        'common_ids': len(common),
        'ids_same_features': sum(by_id[0][i]['feature_sha256_float32'] == by_id[1][i]['feature_sha256_float32'] for i in common),
        'ids_same_module_proxy': sum(by_id[0][i]['module_group_proxy'] == by_id[1][i]['module_group_proxy'] for i in common),
        'feature_or_group_disagreement_ids': [i for i in common if by_id[0][i]['feature_sha256_float32'] != by_id[1][i]['feature_sha256_float32'] or by_id[0][i]['module_group_proxy'] != by_id[1][i]['module_group_proxy']]}
    _, rows, graph = tasks[0]
    groups = sorted({x['module_group_proxy'] for x in rows if x['module_group_proxy'] is not None}, key=lambda name: text_hash('geneda-integrity-v1:' + name))
    n = len(groups)
    a, b = int(0.6 * n), int(0.8 * n)
    group_splits = {'train': groups[:a], 'validation': groups[a:b], 'test': groups[b:]}
    manifest = {'protocol': 'v1', 'source_commit': COMMIT, 'purpose': 'Educational grouping and connector-integrity fixtures; not original paper split',
                'group_field': 'module_group_proxy', 'true_parent_design_provenance_verified': False,
                'groups': group_splits, 'caps': {'train': 96, 'validation': 32, 'test': 32}, 'rows': {}, 'excluded_cross_split_duplicate_ids': []}
    arrays, seen = {}, set()
    for split, group_names in group_splits.items():
        candidates = [x for x in rows if x['module_group_proxy'] in group_names and x['id'] not in cross['feature_or_group_disagreement_ids']]
        candidates.sort(key=lambda row: text_hash(str(row['id'])))
        keep = []
        for row in candidates:
            if row['feature_sha256_float32'] in seen:
                manifest['excluded_cross_split_duplicate_ids'].append(row['id'])
            elif len(keep) < manifest['caps'][split]:
                keep.append(row)
        seen.update(x['feature_sha256_float32'] for x in keep)
        manifest['rows'][split] = [{k: row[k] for k in ['row', 'id', 'module_group_proxy', 'feature_sha256_float32', 'label_sha256']} for row in keep]
        arrays[split] = np.asarray([graph[row['row']]['graph'] for row in keep], dtype=np.float32).reshape(-1, 768)
        arrays[split + '_ids'] = np.asarray([row['id'] for row in keep], dtype=np.int64)
    np.savez_compressed(HERE / 'results' / 'fixture_features.npz', **arrays)
    manifest_raw = json.dumps(manifest, indent=2, sort_keys=True) + '\n'
    (HERE / 'results' / 'split_manifest.json').write_text(manifest_raw)
    upstream = HERE / 'upstream'
    upstream.mkdir(exist_ok=True)
    source_files = {}
    for name, path in {
        'projector_builder.py': 'model/embed_align/model/model/multimodal_projector/builder.py',
        'llava_arch.py': 'model/embed_align/model/model/llava_arch.py',
        'train.py': 'model/embed_align/model/train/train.py',
    }.items():
        raw = cached_blob(path)
        (upstream / name).write_bytes(raw)
        source_files[name] = {'original_path': path, 'sha256': digest(raw), 'url': f'https://github.com/hkust-zhiyao/GenEDA/blob/{COMMIT}/{path}', 'modified': False}
    metrics = {'source_commit': COMMIT, 'tasks': [x[0] for x in tasks], 'cross_task': cross,
               'educational_split_sizes': {s: len(v) for s, v in manifest['rows'].items()},
               'split_manifest_sha256': digest(manifest_raw.encode()), 'source_files': source_files,
               'elapsed_seconds': time.monotonic() - start}
    (HERE / 'results' / 'integrity.json').write_text(json.dumps(metrics, indent=2) + '\n')
    (HERE / 'results' / 'pairing_map.json').write_text(json.dumps({f'task{i + 1}': t[1] for i, t in enumerate(tasks)}, indent=2) + '\n')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
