"""Exhaustive combinatorial identities; no stochastic/model observations."""
from itertools import combinations, product
from math import comb
import json
from pathlib import Path
from tau2.metrics.agent_metrics import pass_hat_k

checks=0
example=[]
for n in range(1,7):
    for bits in product((0,1), repeat=n):
        c=sum(bits)
        for k in range(1,n+1):
            subsets=list(combinations(bits,k))
            all_success=sum(all(x) for x in subsets)/len(subsets)
            any_success=sum(any(x) for x in subsets)/len(subsets)
            assert abs(pass_hat_k(n,c,k)-all_success)<1e-12
            at_k=1-comb(n-c,k)/comb(n,k) if n-c>=k else 1.0
            assert abs(at_k-any_success)<1e-12
            checks+=1
for k in range(1,5):
    example.append({'n':4,'c':2,'k':k,'pass_power_k':pass_hat_k(4,2,k),'pass_at_k':1-comb(2,k)/comb(4,k) if k<=2 else 1.0})
result={'status':'reference_calibration','purpose':'exact enumeration of metric formulas only; not model reliability','checks':checks,'example':example,'performance_estimates':None,'confidence_intervals':None}
Path('/out/metrics-formulas.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
