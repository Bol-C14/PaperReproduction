"""Cross-check retained scientific artifacts; fails if incomplete/inconsistent."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((root/p).read_text())
rows=read('results/pilot_candidates.json');sat=read('results/rtl_equivalence.json');queries=read('results/search_queries.json');summary=read('results/search_summary.json')
assert len(rows)==68 and len(sat)==68 and all(r['passed'] for r in sat)
assert {r['id'] for r in rows}=={r['id'] for r in sat}
for r in rows:
 src=root/f"results/rtl/{r['id']}.v";assert hashlib.sha256(src.read_bytes()).hexdigest()==r['rtl_sha256']
 miter=(root/f"results/rtl/{r['id']}_miter.v").read_text();assert miter.startswith(src.read_text().replace('module top(','module dut('))
 assert r['proof']=='unsat'
 net=root/f"results/netlists/{r['id']}.json"
 if net.exists():assert hashlib.sha256(net.read_bytes()).hexdigest()==r['netlist_sha256']
assert len(queries)==720 and len(summary)==180
sessions={}
for r in queries:sessions.setdefault((r['width'],tuple(r['constants']),r['seed'],r['method']),[]).append(r['id'])
assert all(len(v)==4 and len(set(v))==4 for v in sessions.values())
ra=read('results/rule_audit.json');assert len(ra)==90 and sum(r['result']=='sat' for r in ra)==21 and all(r['result']!='unknown' for r in ra)
print('PASS: 68 RTL/source/proof/hash records; 68 SAT results; 180 four-query sessions; 90 rule checks.')
