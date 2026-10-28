"""Fetch only public, pinned training AIGs; never retry failed requests."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--protocol', type=Path, required=True)
args = parser.parse_args()
protocol = json.loads(args.protocol.read_text())
assets = args.root / 'assets/abc-rl'
manifest = args.root / 'results/abc-rl/ablation-assets.json'
assert not manifest.exists(), 'No implicit retry or overwrite'
rows = []
for name in protocol['source_train_bank']:
    path = assets / (name+'.aig')
    url = f'https://raw.githubusercontent.com/NYU-MLDA/ABC-RL/{protocol["upstream_sha"]}/arithmetic/{name}.aig'
    row = dict(name=name, url=url, cached=path.exists())
    try:
        if not path.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                payload = response.read(100_000_001)
            assert len(payload) < 100_000_001 and payload.startswith(b'aig ')
            path.write_bytes(payload)
        payload = path.read_bytes()
        assert payload.startswith(b'aig ')
        row.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), status='ok')
    except Exception as exc:
        row.update(status='failed', error=repr(exc))
        rows.append(row)
        manifest.write_text(json.dumps(rows, indent=2)+'\n')
        raise
    rows.append(row)
    manifest.write_text(json.dumps(rows, indent=2)+'\n')
    print(name, row['bytes'], flush=True)
    time.sleep(.1)
