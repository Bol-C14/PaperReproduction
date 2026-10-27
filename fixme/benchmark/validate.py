"""Check evaluator control expectations and trace integrity, not model accuracy."""
import collections,hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1]);r=json.loads((p/'results.json').read_text());xs={(x['subset'],x['variant']):x for x in r['results']}
for s in ['SpeCom','MGen','TBGen','SVAGen','RTLFix','RTLFixText']:
 assert xs[s,'positive']['status']=='pass',(s,'positive')
 for v in ['wrong','malformed']:assert xs[s,v]['status']=='fail',(s,v)
assert xs['TBGen','timeout']['status']=='unknown'
assert xs['SVAGen','unsupported']['status']=='unsupported'
assert xs['SVAGen','vacuous']['status']=='unknown'
assert xs['TBGen','empty_tb']['status']=='fail' and xs['TBGen','empty_tb']['official_status']=='pass'
assert xs['TBGen','positive']['mutation_killed'] and not xs['TBGen','empty_tb']['mutation_killed']
assert xs['RTLFix','wrong']['official_status']=='pass'
assert r['formal_parser_checks']['# found: 0\n# proven: 0']=='inconclusive'
assert r['formal_parser_checks']['# found: 2\n# proven: 1']=='inconclusive'
assert xs['SVAGen','positive']['property_counts']['assert'] > 0
assert xs['SVAGen','positive']['mutation_killed'] is True
assert xs['SVAGen','vacuous'].get('mutation_killed') is False
assert r['live_llm'] is False and r['pass_at_5'] is None
for x in r['results']:
 raw=(p/(x['subset']+'_'+x['variant'])/'response.txt').read_bytes();assert hashlib.sha256(raw).hexdigest()==x['response_sha256']
for e in map(json.loads,(p/'trace.jsonl').read_text().splitlines()):assert (p/e['log']).exists()
assert 'PermissionError' in next((p/'isolation_probe').glob('*log')).read_text()
# Independently recount emitted design cells; no fixture-label-based scoring.
from evaluation import property_counts
assert property_counts(p/'SVAGen_positive'/'formal.json')['assert'] > 0
if len(sys.argv)>2:
 reg=pathlib.Path(sys.argv[2]);record=json.loads((reg/'regression.json').read_text())
 assert record['passed'] and len(record['checks'])==45 and all(c['passed'] for c in record['checks'])
 swapped=json.loads((reg/'response_swap'/'results.json').read_text())
 sr={x['variant']:x for x in swapped['results']}
 assert sr['positive']['status']=='unknown'
 assert property_counts(reg/'response_swap'/'SVAGen_positive'/'formal.json')['assert']==0
 assert any('SUCCESS!' in x.read_text() for x in (reg/'response_swap'/'SVAGen_positive').glob('*formal.log'))
 assert sr['wrong']['status']==sr['unsupported']['status']=='pass'
 assert sr['malformed']['status']=='unknown' and sr['vacuous']['status']=='unsupported'
 dpi=json.loads((reg/'dpi_execution'/'results.json').read_text())
 assert {x['variant']:x['status'] for x in dpi['results']}=={'positive':'unknown','wrong':'error','malformed':'pass'}
 for folder in ['response_swap','missing_tool','dpi_execution']:
  rp=reg/folder
  for x in json.loads((rp/'results.json').read_text())['results']:
   raw=(rp/(x['subset']+'_'+x['variant'])/'response.txt').read_bytes()
   assert hashlib.sha256(raw).hexdigest()==x['response_sha256']
  for e in map(json.loads,(rp/'trace.jsonl').read_text().splitlines()):assert (rp/e['log']).exists()
 for e in map(json.loads,(reg/'trace.jsonl').read_text().splitlines()):assert (reg/e['log']).exists()
 print('PASS: 45 regression checks, swapped responses, actual zero/nonzero property counts, DPI timeout/crash states and trace integrity')
print('PASS: six positive paths, 12 wrong/malformed controls, timeout, unsupported, vacuity, mutation, parser, trace and network-denial checks')
