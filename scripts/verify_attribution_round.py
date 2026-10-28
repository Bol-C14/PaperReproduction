"""Recompute retained round artifacts/controller path without EDA or model calls."""
import collections,gzip,hashlib,json,os,random
from pathlib import Path
from attribution_round import *
read=lambda p:json.loads(p.read_text())
v=read(O/'validation.json');assert v['total_synthesis']==57 and v['eda_ledger_entries']==114
inventory=read(O/'unique_netlist_inventory.json');assert len(inventory)==28
by_rtl={r['rtl_sha256']:r for r in inventory}
for row in inventory:
 p=O/row['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['netlist_sha256'];dummy=metrics_and_attribution(p,O/'rtl'/f"{row['representative_id']}.v",{});assert (dummy['gates'],dummy['depth'])==(row['gates'],row['depth'])
replayed=0
for p in sorted((O/'sessions').glob('*.json')):
 s=read(p);g=read(O/'graphs'/f"{s['fixture']}.json");costs=initial_costs(g);accepted=dict(costs);best=float('inf');seen=set();rng=random.Random(0)
 for ident in s['record_ids']:
  r=read(O/'runs'/f'{ident}.json');cand=novel(g,costs,seen,s['width']);assert cand;_,ex,search=cand;text,lines,*_=tagged(g,ex,s['width']);m=r['metrics'];h=hashlib.sha256(text.encode()).hexdigest();assert h==m['rtl_sha256'] and h not in seen;seen.add(h)
  assert (O/'rtl'/f'{ident}.v').read_text()==text;assert 'SUCCESS!' in gzip.decompress((L/f'{ident}_rtl_sat.log.gz').read_bytes()).decode()
  a=cone_attribution(O/by_rtl[h]['path'],g,ex);assert abs(a['coverage']-m['coverage'])<1e-9
  for n,val in a['attribution'].items():assert abs(val-m['attribution'][n])<1e-7
  if s['policy']=='random':costs={n:rng.choice([.25,1,3,10]) if x['op'] in OPS else 0 for n,x in g['nodes'].items()}
  elif s['policy']=='openloop':costs,_=structural_update(g,costs,ex)
  elif s['policy']=='numerical':
   if m['gates']>best:
    before=dict(costs);costs=dict(accepted);a=novel(g,costs,seen,s['width']);b=novel(g,before,seen,s['width'])
    ha=hashlib.sha256(tagged(g,a[1],s['width'])[0].encode()).hexdigest() if a else None;hb=hashlib.sha256(tagged(g,b[1],s['width'])[0].encode()).hexdigest() if b else None
    assert ha==r['action']['actual_successor_rtl_sha'] and hb==r['action']['counterfactual_no_rollback_successor_rtl_sha']
    if r['query']<5:assert json.loads((O/'runs'/f"{s['record_ids'][r['query']+1]}.json").read_text())['metrics']['rtl_sha256']==ha
   else:best=m['gates'];accepted=dict(costs);costs,_=numerical_update(costs,m,s['width'])
  assert costs==r['costs_after'];replayed+=1
assert replayed==48
ledger=[json.loads(l) for l in (L/'eda_invocations.jsonl').read_text().splitlines()];assert len(ledger)==114
assert collections.Counter(r['kind'] for r in ledger)=={'synthesis':57,'rtl_sat':57} and all(r['returncode']==0 for r in ledger)
for r in ledger:
 if r['kind']=='rtl_sat':assert 'SUCCESS!' in gzip.decompress((L/f"{r['id']}_rtl_sat.log.gz").read_bytes()).decode()
print('PASS 57 synthesis +57 generated-RTL SAT logs; 28 raw JSON hashes/gate-depth pairs; 48 controller extractions/updates and cone allocations replayed; zero new EDA/model calls. Netlist equivalence not asserted.')
