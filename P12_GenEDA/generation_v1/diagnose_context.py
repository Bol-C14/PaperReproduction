"""Own-checkpoint, train-only adequacy diagnostic; no training and no APIs."""
import json
from pathlib import Path

import numpy as np
import torch

import run_generation as g

HERE = Path(__file__).resolve().parent


def main():
    data = g.prepare_data()['train'][:16]
    reports = []
    for seed in [17, 23]:
        decoder = g.Decoder()
        with np.load(HERE / f'results_g2/base_seed{seed}.npz', allow_pickle=False) as archive:
            decoder.load_state_dict({name: torch.from_numpy(archive[name].copy()) for name in archive.files})
        decoder.setup('frozen')
        decoder.eval()
        records = []
        with torch.no_grad():
            for row in data:
                direct_ids, direct_labels, _ = g.batch([row], [0], language_only=True)
                prompt_ids, prompt_labels, _ = g.batch([row], [0])
                direct = g.loss(decoder(direct_ids)[0], direct_labels).item()
                context = g.loss(decoder(prompt_ids, torch.zeros(1, g.D))[0], prompt_labels).item()
                records.append({'id': row['id'], 'answer_only_nll': direct, 'prompt_zero_graph_nll': context})
        reports.append({'seed': seed, 'rows': records,
                        'mean_answer_only_nll': float(np.mean([x['answer_only_nll'] for x in records])),
                        'mean_prompt_zero_graph_nll': float(np.mean([x['prompt_zero_graph_nll'] for x in records]))})
    result = {'scope': 'Same 16 training answers; own prealignment scratch decoder; joint context/position contrast, not a causal identification of positional failure', 'seeds': reports}
    g.write_json(HERE / 'results_g2/context_diagnostic.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
