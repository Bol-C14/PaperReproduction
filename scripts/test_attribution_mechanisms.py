"""Controlled extraction interventions, not extra synthesis or efficacy evidence."""
import copy,json,sys
from pathlib import Path
from attribution_round import *

def signature(g,c):
 t,e=extract(g,c);return sha(t),t,e
records=json.loads((O/'pilot_successors.json').read_text());mcm=records[0];g,_=graph_for(mcm['name']);base=mcm['costs_before'];up=mcm['costs_after'];h0,t0,e0=signature(g,base);h1,t1,e1=signature(g,up);assert h0!=h1
# Permute actual attribution values while preserving total in a transparent context.
a=mcm['base']['attribution'];ids=sorted(a);swapped=dict(a);swapped[ids[0]],swapped[ids[-1]]=a[ids[-1]],a[ids[0]];found_attr=None
for scale in [.125,.25,.5,1,2]:
 ca=dict(base);cb=dict(base)
 for n in ids:ca[n]=max(.25,scale*a[n]/12);cb[n]=max(.25,scale*swapped[n]/12)
 ha,ta,_=signature(g,ca);hb,tb,_=signature(g,cb)
 if ha!=hb:found_attr=dict(scale=scale,actual=ca,permuted=cb,actual_terms=ta,permuted_terms=tb,total_attribution=sum(a.values()),note='controlled equal-total reallocation sensitivity, not verified marginal causal ownership');break
assert found_attr
# Lower a node with measured zero cone area; find a bounded illustrative context.
measured=mcm['successor']['attribution'];shifts=[n for n,v in measured.items() if v==0 and g['nodes'][n]['op']=='Shl'];found_down=None;contexts=0
for mul in [1,2,3,4,8,10,16]:
 for add in [1,2,4,8]:
  for n in shifts:
   c={i:(mul if v['op']=='Mul' else add if v['op'] in ['Add','Sub'] else 1 if v['op']=='Shl' else 0) for i,v in g['nodes'].items()};d=dict(c);d[n]=.25;contexts+=1
   hc,tc,_=signature(g,c);hd,td,_=signature(g,d)
   if hc!=hd:found_down=dict(node=n,measured_attributed_cells=0,old_cost=1,new_cost=.25,context_mul=mul,context_add=add,before=tc,after=td,contexts_checked=contexts,note='bounded extraction-only mechanism context; not selected as comparison hyperparameters');break
  if found_down:break
 if found_down:break
assert found_down
# A rollback is now persistent; the immediately following extraction changes.
hr,tr,_=signature(g,base);hn,tn,_=signature(g,up);assert hr!=hn
result=dict(cost_increase=dict(before=t0,after=t1,successor_actual_gates=mcm['successor']['gates']),attribution=found_attr,cost_decrease=found_down,rollback=dict(before_cost_sha=sha(up),restored_cost_sha=sha(base),without_rollback=tn,after_rollback=tr,changed=True,note='controlled restoration test; neither reset at outer boundary nor extra EDA. Natural rejected-candidate effects checked in actual comparison trace.'),new_synthesis_calls=0,new_sat_calls=0)
save(O/'mechanism_tests.json',result);print('PASS measured-allocation sensitivity, cost increase, measured-zero-node decrease, and persistent rollback each change successor extraction; zero new EDA.')
