"""Single targeted asset diagnostic authorized in DIAGNOSTIC_ADDENDUM.md."""
import json
from pathlib import Path

import numpy as np

from check_assets import cached_blob

HERE = Path(__file__).resolve().parent


def summarize(a):
    def unique(v):
        return len({row.tobytes() for row in v})
    delta = np.linalg.norm(a.astype(np.float64) - a[0].astype(np.float64), axis=1)
    base = float(np.linalg.norm(a[0].astype(np.float64)))
    absmax = float(np.abs(a).max())
    ranges = np.ptp(a.astype(np.float64), axis=0)
    return dict(rows=len(a), width=a.shape[1], unique_float64=unique(a.astype(np.float64)),
                unique_float32=unique(a.astype(np.float32)), unique_float16=unique(a.astype(np.float16)),
                first_vector_l2=base, max_l2_distance_from_first=float(delta.max()),
                max_relative_l2_distance_from_first=float(delta.max() / base),
                max_coordinate_range=float(ranges.max()), median_coordinate_range=float(np.median(ranges)),
                max_abs_feature=absmax,
                max_range_over_epsilon32_times_max_feature=float(ranges.max() / (np.finfo(np.float32).eps * absmax)))


if __name__ == '__main__':
    rows = json.loads(cached_blob('benchmark/task1/data/Task1_summary_GenEDA.json'))
    data = np.asarray([row['graph'] for row in rows], dtype=np.float64)
    fixtures = np.load(HERE / 'results' / 'fixture_features.npz', allow_pickle=False)['train'][:16]
    metrics = {'scope': 'Released asset discriminability only; no original encoder inference or retraining',
               'full_task1': summarize(data), 'synthetic_training_fixture16': summarize(fixtures)}
    (HERE / 'results' / 'feature_discriminability.json').write_text(json.dumps(metrics, indent=2) + '\n')
    print(json.dumps(metrics, indent=2))
