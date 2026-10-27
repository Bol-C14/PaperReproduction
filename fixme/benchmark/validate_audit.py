"""Validate the all-case asset audit against original bytes, not model metrics."""
import argparse,collections,csv,hashlib,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--upstream',required=True);p.add_argument('--audit',required=True);a=p.parse_args();u=pathlib.Path(a.upstream);base=pathlib.Path(a.audit);r=json.loads((base/'audit.json').read_text());rows=r['cases']
assert len(rows)==len({x['id'] for x in rows})==482
assert len(list(csv.DictReader((base/'coverage.csv').open())))==482
for row in rows:
 for f in row['input_files']:
  path=u/'data'/row['id']/f['name'];assert path.stat().st_size==f['bytes'];assert hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256']
 for o in row['structural_overlays']:
  path=u/o['source'];assert hashlib.sha256(path.read_bytes()).hexdigest()==o['sha256']
  if 'matched_rtl_sha256' in o:
   assert o['matched_rtl_sha256'] in {f['sha256'] for f in row['input_files']}
 for c in row.get('reference_controls',[]):assert hashlib.sha256(c['response'].encode()).hexdigest()==c['response_sha256']
assert sum(x['schema_complete'] for x in rows)==403
assert sum(x['adapted_schema_complete'] for x in rows)==430
assert sum(x['prior_pilot_input'] for x in rows)==6
assert sum(x['eda_state']=='bounded_prior_fixed_response_pilot_executed' for x in rows)==4
assert sum('reference_controls' in x for x in rows)==251
assert sum(x.get('complete_task_reference_checked',False) for x in rows)==199
states=collections.Counter((c['label'],c['status']) for row in rows for c in row.get('reference_controls',[]))
assert states=={('reference_positive','pass'):200,('wrong','fail'):200,('malformed','fail'):200,('reference_positive','error'):51,('wrong','error'):51,('malformed','error'):51}
assert len({x['data_tree'] for x in r['history']})==1 and len(r['history'])==5
assert len(r['test_tree']['file_comparisons'])==56 and all(x['identical_bytes'] for x in r['test_tree']['file_comparisons'])
assert r['test_tree']['case_directories']==20 and not r['test_tree']['additional_case_keys']
assert r['git_checks']['shallow']=='false' and not r['git_checks']['submodules'] and not r['git_checks']['lfs_pointers'] and not r['git_checks']['archives']
print('PASS: all 482 case records/input hashes; 403 original and 430 adapted schemas; 753 reference controls; five identical historical data trees; 56 duplicate test files')
