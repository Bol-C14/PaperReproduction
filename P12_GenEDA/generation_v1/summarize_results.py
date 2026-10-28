"""Summarize completed frozen runs; do not fit or select models."""
import collections
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent


def main():
    protocols = {}
    for protocol, folder in [('G1', 'results'), ('G2', 'results_g2')]:
        root = HERE / folder
        paths = sorted(root.glob('run_*.json'))
        assert len(paths) == 10, f'Incomplete protocol {protocol}: {len(paths)} arms'
        evaluation = json.loads((root / 'evaluation.json').read_text())
        rows = evaluation['summaries']
        grouped = collections.defaultdict(list)
        for row in rows:
            if row['split'] == 'test':
                grouped[(row['arm'], row['intervention'])].append(row)
        means = []
        for (arm, intervention), subset in sorted(grouped.items()):
            means.append({'arm': arm, 'intervention': intervention, 'seeds': [r['seed'] for r in subset],
                          'rouge_l_f1': statistics.mean(r['rouge_l_f1'] for r in subset),
                          'functional_terms_f1': statistics.mean(r['functional_terms_f1'] for r in subset if r['functional_terms_f1'] is not None),
                          'exact_prefix_match_rate': statistics.mean(r['exact_prefix_match'] for r in subset),
                          'byte_trigram_repetition': statistics.mean(r['repeated_byte_trigram_fraction'] for r in subset),
                          'references_with_functional_terms_per_seed': [r['references_with_functional_terms'] for r in subset]})
        counterfactuals = []
        resources = []
        for seed in [17, 23]:
            resources.append(json.loads((root / f'resources_seed{seed}.json').read_text()))
            for arm in ['raw_matched', 'normalized_matched']:
                run = json.loads((root / f'run_{seed}_{arm}.json').read_text())
                examples = {(r['id'], r['intervention']): r for r in run['generations'] if r['split'] == 'test'}
                ids = sorted({key[0] for key in examples})
                for intervention in ['remove', 'shuffle']:
                    identical = sum(examples[i, 'none']['generated'] == examples[i, intervention]['generated'] for i in ids)
                    counterfactuals.append({'seed': seed, 'arm': arm, 'intervention': intervention,
                                           'n': len(ids), 'identical_output_count': identical,
                                           'changed_output_count': len(ids) - identical})
        seeds = []
        for seed in [17, 23]:
            by_arm = {r['arm']: r for r in rows if r['seed'] == seed and r['split'] == 'test' and r['intervention'] == 'none'}
            for arm, comparison in [('raw_matched', 'zero_modality'), ('normalized_matched', 'normalized_shuffled'), ('normalized_matched', 'zero_modality'), ('normalized_matched', 'text_sft'), ('normalized_matched', 'generic_template')]:
                seeds.append({'seed': seed, 'arm': arm, 'comparison': comparison,
                              'rouge_l_delta': by_arm[arm]['rouge_l_f1'] - by_arm[comparison]['rouge_l_f1'],
                              'functional_f1_delta': by_arm[arm]['functional_terms_f1'] - by_arm[comparison]['functional_terms_f1']})
        protocols[protocol] = {'averages_over_two_seeds': means, 'seed_contrasts': seeds,
                               'counterfactual_output_changes': counterfactuals,
                               'resources': resources,
                               'split_manifest_sha256': hashlib.sha256((root / 'split_manifest.json').read_bytes()).hexdigest()}
    assert protocols['G1']['split_manifest_sha256'] == protocols['G2']['split_manifest_sha256']
    output = {'protocols': protocols, 'context_diagnostic': json.loads((HERE / 'results_g2/context_diagnostic.json').read_text()),
              'limits': ['Scratch decoder, not original pretrained GenEDA', 'One training project family, 16 test examples', 'Original encoder pretraining exposure unverified',
                         'Lexical metrics are not circuit-functional correctness', 'No significance claim from two seeds']}
    (HERE / 'summary.json').write_text(json.dumps(output, indent=2) + '\n')
    for protocol, info in protocols.items():
        print(protocol)
        for row in info['averages_over_two_seeds']:
            if row['intervention'] == 'none':
                print(row['arm'], round(row['rouge_l_f1'], 6), round(row['functional_terms_f1'], 6))
        print('seconds', sum(r['wall_seconds'] for r in info['resources']), 'peak_kib', max(r['peak_rss_kib'] for r in info['resources']))


if __name__ == '__main__':
    main()
