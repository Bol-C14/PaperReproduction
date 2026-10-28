"""Validate completed run accounting, leakage guards and independent scores."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


if __name__ == '__main__':
    checks = []
    for folder, pretrain, stage1, stage2 in [('results', 160, 40, 80), ('results_g2', 1600, 120, 240)]:
        root = HERE / folder
        manifest = json.loads((root / 'split_manifest.json').read_text())
        ids = {split: {r['id'] for r in rows} for split, rows in manifest['records'].items()}
        assert list(map(len, [ids['train'], ids['validation'], ids['test']])) == [64, 16, 16]
        for field in ['family', 'feature_hash', 'normalized_target_hash']:
            sets = [{r[field] for r in manifest['records'][s]} for s in ['train', 'validation', 'test']]
            assert all(not sets[i] & sets[j] for i in range(3) for j in range(i+1, 3))
        for seed in [17, 23]:
            budget = json.loads((root / f'budgets_seed{seed}.json').read_text())
            assert len(budget['task_batch_ids']) == stage1 + stage2
            assert len(budget['pretraining_batch_ids']) == pretrain
            assert all(set(batch) <= ids['train'] for batch in budget['task_batch_ids'] + budget['pretraining_batch_ids'])
            assert all(int(k) != v and v in ids['train'] for k, v in budget['shuffle_mapping_ids'].items())
            for arm in ['raw_matched', 'normalized_matched', 'normalized_shuffled', 'zero_modality', 'text_sft']:
                run = json.loads((root / f'run_{seed}_{arm}.json').read_text())
                assert [s['steps'] for s in run['stage_budgets']] == [stage1, stage2]
                assert len(run['task_trace']) == stage1 + stage2
                natural = [r for r in run['generations'] if r['split'] == 'test' and r['intervention'] == 'none']
                assert {r['id'] for r in natural} == ids['test']
                assert len(natural) == 16
        evaluation = json.loads((root / 'evaluation.json').read_text())
        assert len(evaluation['per_example']) == 392
        assert all(0 <= r['rouge_l_f1'] <= 1 for r in evaluation['per_example'])
        checks.append({'folder': folder, 'runs': 10, 'scored_examples_including_interventions_and_baselines': 392,
                       'family_and_exact_duplicate_leakage_checks': 'pass', 'budgets_and_seed_accounting': 'pass'})
    (HERE / 'output_checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    print(json.dumps(checks, indent=2))
