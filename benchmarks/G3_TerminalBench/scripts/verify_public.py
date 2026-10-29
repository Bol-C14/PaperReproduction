"""Offline public-payload checks. Requires the privately retained original tree."""
import hashlib
import json
from pathlib import Path
import re
from public_sanitize import public_view

B=Path(__file__).resolve().parents[1]
O=B/'.private/sanitization/original-public-tree/benchmarks/G3_TerminalBench'
original_manifest=json.loads((O/'manifest.json').read_text())
private_root=original_manifest['remote_root']

def check_numbers(old,new):
    if isinstance(old,dict):
        for k,v in old.items(): check_numbers(v,new[k])
    elif isinstance(old,list):
        assert len(old)==len(new)
        for a,b in zip(old,new): check_numbers(a,b)
    elif isinstance(old,(int,float,bool)) or old is None:
        assert type(old)==type(new) and old==new,(old,new)

numeric=0
for name in ['manifest.json','metrics/calibration.json','logs/SUMMARY_VERIFICATION.json','logs/EVIDENCE_VERIFICATION.json']:
    a=json.loads((O/name).read_text());b=json.loads((B/name).read_text())
    check_numbers(public_view(a,private_root),b)
    old_hashes=sorted(re.findall(r'(?<![a-f0-9])[a-f0-9]{64}(?![a-f0-9])',json.dumps(a)))
    new_hashes=sorted(re.findall(r'(?<![a-f0-9])[a-f0-9]{64}(?![a-f0-9])',json.dumps(b)))
    assert old_hashes==new_hashes,name
    numeric+=1
for name in ['metrics/resource_comparison.csv','logs/SUMMARY_VERIFICATION.json','logs/EVIDENCE_VERIFICATION.json']:
    assert (O/name).read_bytes()==(B/name).read_bytes(),name
archive=B/'.private/raw-evidence.tar.gz'
raw_sha=hashlib.sha256(archive.read_bytes()).hexdigest()
assert raw_sha in (O/'RAW_EVIDENCE.md').read_text()
paths=[x for x in (B/'PUBLIC_WHITELIST.txt').read_text().splitlines() if x]
for rel in paths:
    p=B.parents[1]/rel
    assert p.is_file(),rel
    assert '/.private/' not in rel and '/__pycache__/' not in rel
    text=p.read_text()
    assert private_root not in text,rel
    assert re.search(r'/(?:home|Users)/[^/\s]+',text) is None,rel
    assert re.search(r'/tmp/tmp[a-zA-Z0-9_]+',text) is None,rel
    assert not rel.endswith(('solve.sh','test_outputs.py','test.py','regex.txt','summary.csv','run.py'))
print(json.dumps({'numeric_json_documents_preserved':numeric,'all_64_hex_evidence_tokens_preserved':True,'resource_csv_and_evidence_logs_byte_identical':True,'raw_archive_sha256':raw_sha,'whitelisted_files':len(paths),'forbidden_host_paths':0,'no_experiment_rerun':True},indent=2))
