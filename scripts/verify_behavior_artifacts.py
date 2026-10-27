"""Audit retained online records and replay controller decisions, no new EDA."""
import gzip,hashlib,json,os
from pathlib import Path
from behavior_loop import update_costs,update_costs_openloop,digest
from behavior_engine import initial_costs
R=Path(__file__).resolve().parents[1]/Path(os.environ.get('ASPEN_BEHAVIOR_RUN_ROOT','.'));O=R/'results/behavior';L=R/'logs/behavior'
read=lambda p:json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
sessions=[read(p) for p in (O/'sessions').glob('*.json')];assert len(sessions) in [49,52]
metrics=[];updates=0;open_updates=0
for s in sessions:
 metrics.append((s['id']+'_reference',s['baseline']))
 for outer in range(2):
  graph=read(O/'graphs'/f"{s['id']}_o{outer}.json.gz");costs=initial_costs(graph);best=s['baseline']['gates'];snapshot=None
  for inner in range(3):
   r=read(O/'runs'/f"{s['id']}_o{outer}_i{inner}.json");metrics.append((r['id'],r['metrics']))
   if s['cost']=='feedback':
    costs,act=update_costs(graph,costs,r['extraction'],r['metrics']['gates'],best,snapshot);snapshot=act['snapshot_before_update'];assert costs==r['costs_after'];assert act['delta']==r['action']['delta'] and act['rollback']==r['action']['rollback'];updates+=1
   if s['cost']=='openloop':
    costs,act=update_costs_openloop(graph,costs,r['extraction']);assert costs==r['costs_after'] and not act['rollback'] and act['delta']==3;assert r['action']['response_read'] is False;open_updates+=1
   best=min(best,r['metrics']['gates'])
for r in read(O/'figure4.json')['rows']:
 if r['metrics']:metrics.append(('figure4_'+r['model'],r['metrics']))
assert len(metrics) in [346,367]
for ident,m in metrics:
 assert m['z3']=='unsat' and m['rtl_sat']
 p=O/'rtl'/f'{ident}.v';assert hashlib.sha256(p.read_bytes()).hexdigest()==m['rtl_sha256']
 mit=(O/'rtl'/f'{ident}_miter.v').read_text();assert mit.startswith(p.read_text().replace('module top(','module dut('))
 sat=gzip.decompress((L/f'{ident}_sat.log.gz').read_bytes()).decode();assert 'SUCCESS!' in sat
ledger=[json.loads(l) for l in (L/'eda_invocations.jsonl').read_text().splitlines()];assert len(ledger)==2*len(metrics) and all(r['returncode']==0 for r in ledger)
print(f'PASS {len(metrics)} RTL hashes/UNSAT/SAT logs; {len(ledger)} real EDA ledger entries; {updates} feedback and {open_updates} response-blind decisions replayed; zero new EDA. RTL SAT is RTL-to-reference only, not synthesized netlist equivalence.')
