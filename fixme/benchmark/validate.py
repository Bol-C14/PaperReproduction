"""Check evaluator control expectations and trace integrity, not model accuracy."""
import collections,hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1]);r=json.loads((p/'results.json').read_text());xs={(x['subset'],x['variant']):x for x in r['results']}
for s in ['SpeCom','MGen','TBGen','SVAGen','RTLFix','RTLFixText']:
 assert xs[s,'positive']['status']=='pass',(s,'positive')
 for v in ['wrong','malformed']:assert xs[s,v]['status']=='fail',(s,v)
assert xs['TBGen','timeout']['status']=='unknown'
assert xs['SVAGen','unsupported']['status']=='unsupported'
assert xs['SVAGen','vacuous']['status']=='fail'
assert xs['TBGen','empty_tb']['status']=='fail' and xs['TBGen','empty_tb']['official_status']=='pass'
assert xs['TBGen','positive']['mutation_killed'] and not xs['TBGen','empty_tb']['mutation_killed']
assert xs['RTLFix','wrong']['official_status']=='pass'
assert r['formal_parser_checks']['# found: 0\n# proven: 0']=='inconclusive'
assert r['formal_parser_checks']['# found: 2\n# proven: 1']=='inconclusive'
assert r['live_llm'] is False and r['pass_at_5'] is None
for x in r['results']:
 raw=(p/(x['subset']+'_'+x['variant'])/'response.txt').read_bytes();assert hashlib.sha256(raw).hexdigest()==x['response_sha256']
for e in map(json.loads,(p/'trace.jsonl').read_text().splitlines()):assert (p/e['log']).exists()
assert 'PermissionError' in next((p/'isolation_probe').glob('*log')).read_text()
print('PASS: six positive paths, 12 wrong/malformed controls, timeout, unsupported, vacuity, mutation, parser, trace and network-denial checks')
