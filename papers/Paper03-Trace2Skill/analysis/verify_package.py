#!/usr/bin/env python3
"""Verify retained upstream bytes and deliverable consistency, never execute unknown scripts."""
import hashlib,json,tarfile
from pathlib import Path
P=Path(__file__).resolve().parents[1];U=next((P/'upstream').iterdir())
source_count=0
with tarfile.open(P/'sources/github-5702b3f.tar.gz') as archive:
 for m in archive.getmembers():
  if m.isfile():
   rel=Path(*Path(m.name).parts[1:]);data=archive.extractfile(m).read();assert (U/rel).read_bytes()==data,rel;source_count+=1
r=json.loads((P/'metrics/independent_audit.json').read_text());o=json.loads((P/'metrics/official_validation.json').read_text());b=json.loads((P/'metrics/replay.json').read_text())
for c in ['C3','C4']:
 assert r[c]['passes']==o[c]['passes'] and r[c]['n']==o[c]['rollouts']
 assert r[c]['feedback_executions']==o[c]['feedback_audit']['executions']
assert len(b['tests'])==19 and all(t['status']=='pass' for t in b['tests'])
assert len(b['traces'])==2 and len({t['skill_sha256'] for t in b['traces']})==1
for f in ['REPRODUCTION.md','EVIDENCE_AUDIT.md','BASELINE_COMPARISON.md','RESEARCH_OPPORTUNITIES.md']:
 assert len((P/f).read_bytes())>1000
print(json.dumps(dict(upstream_files_byte_identical=source_count,helper_tests_passed=len(b['tests']),official_independent_counts_agree=True,live_rollouts=0),indent=2))
