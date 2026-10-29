"""Recount reward components offline without reading answers or making network calls."""
from pathlib import Path
from collections import Counter
import json
import hashlib
import argparse

package = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, help='Optional authorized pinned tasks.json for extraction verification; never printed')
args = parser.parse_args()
inv = json.loads((package/'results/reward-basis-inventory.json').read_text())
audit = json.loads((package/'results/source-audit.json').read_text())
assert set(inv) == {'source_commit', 'source_path', 'source_sha256', 'rows'}
assert inv['source_commit'] == audit['paper_commit'] == '37199f36924c8896f5e048360691f8476cd89ba1'
assert inv['source_sha256'] == audit['datasets']['tasks.json']['sha256'] == '192a2c143b3b512c37c3775fdf6c5040c33717388620c38b140c731dc6153cd7'
assert len(inv['rows']) == 114
assert len({r['task_id'] for r in inv['rows']}) == 114
for r in inv['rows']:
    assert set(r) == {'task_id', 'required_components'}
    assert set(r['required_components']) <= {'ENV_ASSERTION', 'ACTION'}
counts = Counter(tuple(r['required_components']) for r in inv['rows'])
assert counts == {('ENV_ASSERTION',):94, ('ENV_ASSERTION','ACTION'):20}
if args.source:
    data = args.source.read_bytes()
    assert hashlib.sha256(data).hexdigest() == inv['source_sha256']
    extracted = [{'task_id':t['id'], 'required_components':t['evaluation_criteria']['reward_basis']} for t in json.loads(data)]
    assert extracted == inv['rows']
print(json.dumps({'source_commit':inv['source_commit'], 'source_sha256':inv['source_sha256'], 'total':114, 'ENV_ASSERTION_only':94, 'ENV_ASSERTION_plus_ACTION':20, 'source_extraction_verified':bool(args.source)}, indent=2))
