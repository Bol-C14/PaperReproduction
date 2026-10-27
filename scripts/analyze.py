import csv,json,random,itertools,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'results/pilot_candidates.json').read_text());cfg=json.loads((root/'configs/pilot.json').read_text());q=[];summ=[]
fig,axes=plt.subplots(2,3,figsize=(11,6),layout='constrained')
for ax,(key,it) in zip(axes.flat,itertools.groupby(rows,key=lambda r:(r['width'],tuple(r['constants'])))):
 rs=list(it);base=rs[0]['gate_count'];X=np.array([r['features'] for r in rs],float);X=(X-X.mean(0))/(X.std(0)+1e-6);X=np.column_stack([np.ones(len(X)),X]);y=np.array([r['gate_count']/base for r in rs]);D=np.array([r['logic_depth'] for r in rs])
 for seed,method in itertools.product(cfg['seeds'],cfg['methods']):
  rng=random.Random(seed);chosen=[0,rng.choice(list(range(1,len(rs))))]
  while len(chosen)<cfg['budget']:
   rem=[i for i in range(len(rs)) if i not in chosen]
   if method=='random':nxt=rng.choice(rem)
   elif method=='structural':nxt=min(rem,key=lambda i:(3*rs[i]['features'][0]+rs[i]['features'][1]+rs[i]['features'][2],i))
   else:
    A=X[chosen].T@X[chosen]+np.eye(X.shape[1]);inv=np.linalg.inv(A);coef=inv@X[chosen].T@y[chosen]
    pred=X@coef;sd=np.sqrt(np.einsum('ij,jk,ik->i',X,inv,X));nxt=min(rem,key=lambda i:pred[i]-.25*sd[i])
   chosen.append(nxt)
  for step,i in enumerate(chosen):q.append(dict(width=key[0],constants=key[1],seed=seed,method=method,query=step+1,id=rs[i]['id'],gate_count=rs[i]['gate_count']))
  summ.append(dict(width=key[0],constants=key[1],seed=seed,method=method,best_gate_count=min(rs[i]['gate_count'] for i in chosen),best_depth=min(rs[i]['logic_depth'] for i in chosen),normalized_best=min(y[chosen]),oracle_best=min(y),queries=len(chosen)))
 pareto=[r for r in rs if not any(s['gate_count']<=r['gate_count'] and s['logic_depth']<=r['logic_depth'] and (s['gate_count']<r['gate_count'] or s['logic_depth']<r['logic_depth']) for s in rs)]
 ax.scatter(D,[r['gate_count'] for r in rs],color='gray',label='evaluated')
 ps=sorted({(r['logic_depth'],r['gate_count']) for r in pareto});ax.plot(*zip(*ps),color='green',marker='o',label='Pareto');ax.scatter([rs[0]['logic_depth']],[base],marker='*',s=120,color='purple',label='direct RTL');ax.set_title(f'{key[1]}, W={key[0]}');ax.set_xlabel('Generic logic depth');ax.set_ylabel('Generic gate count')
axes[0,0].legend(fontsize=8);fig.savefig(root/'results/pilot_pareto.png',dpi=160);plt.close(fig)
(root/'results/search_queries.json').write_text(json.dumps(q,indent=2));(root/'results/search_summary.json').write_text(json.dumps(summ,indent=2))
aggregate=[]
for method in cfg['methods']:
 ss=[r for r in summ if r['method']==method];aggregate.append(dict(method=method,mean_normalized_best=float(np.mean([r['normalized_best'] for r in ss])),mean_oracle_gap=float(np.mean([r['normalized_best']-r['oracle_best'] for r in ss])),sessions=len(ss),queries_per_session=cfg['budget']))
(root/'results/search_aggregate.json').write_text(json.dumps(aggregate,indent=2))
fig,ax=plt.subplots(figsize=(6,3),layout='constrained');ax.bar([r['method'] for r in aggregate],[r['mean_normalized_best'] for r in aggregate]);ax.set_ylabel('Best gates / direct RTL (lower better)');ax.set_title('Offline replay: budget=4; 6 tasks × 10 seeds');fig.savefig(root/'results/search_comparison.png',dpi=160);plt.close(fig)
h=[]
for key,it in itertools.groupby(rows,key=lambda r:(r['width'],tuple(r['constants']))):
 rs=list(it);base=rs[0];h.append(dict(width=key[0],constants=key[1],direct_gates=base['gate_count'],binary_gates=rs[1]['gate_count'],signed_gates=rs[2]['gate_count'],partial_gates=rs[3]['gate_count'],best_gates=min(r['gate_count'] for r in rs),direct_depth=base['logic_depth'],best_depth=min(r['logic_depth'] for r in rs),candidates=len(rs)))
(root/'results/hypotheses.json').write_text(json.dumps(h,indent=2))
table=list(csv.DictReader((root/'sources/table_ii.csv').open()));a=[]
for r in table:
 row={'benchmark':r['benchmark']}
 for base in ['baseline','rover']:
  for metric in ['area','delay']:row[f'{metric}_over_{base}']=100*(1-float(r[f'aspen_{metric}'])/float(r[f'{base}_{metric}']))
 a.append(row)
means={k:float(np.mean([r[k] for r in a])) for k in a[0] if k!='benchmark'}
(root/'results/table_ii_arithmetic.json').write_text(json.dumps(dict(rows=a,mean=means),indent=2))
print(json.dumps(dict(search=aggregate,hypotheses=h,table_means=means),indent=2))
