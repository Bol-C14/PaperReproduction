"""Replay two saved local NPZ checkpoints; no provider weights or pickle."""
import json
from pathlib import Path

import numpy as np
import torch

import run_generation as g

HERE = Path(__file__).resolve().parent


if __name__ == '__main__':
    row = g.prepare_data()['test'][0]
    results = []
    for arm in ['raw_matched', 'normalized_matched']:
        decoder = g.Decoder()
        decoder.setup('lora')  # Adapter enable flags are code configuration, not tensors.
        model = g.Aligned(decoder, torch.zeros(768), torch.ones(768), arm).eval()
        with np.load(HERE / f'results_g2/model_17_{arm}.npz', allow_pickle=False) as arrays:
            model.load_state_dict({key: torch.from_numpy(arrays[key].copy()) for key in arrays.files})
        text, tokens = g.greedy(model, row)
        saved = json.loads((HERE / f'results_g2/run_17_{arm}.json').read_text())
        expected = next(x for x in saved['generations'] if x['split'] == 'test' and x['id'] == row['id'] and x['intervention'] == 'none')
        equal = text == expected['generated'] and tokens == expected['generated_tokens']
        results.append({'arm': arm, 'seed': 17, 'id': row['id'], 'exact_generation_replayed': equal})
        assert equal, f'Checkpoint replay differs: {arm}'
    g.write_json(HERE / 'results_g2/replay_check.json', results)
    print(json.dumps(results, indent=2))
