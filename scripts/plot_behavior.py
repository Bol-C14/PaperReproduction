import json,os
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]/Path(os.environ.get('ASPEN_BEHAVIOR_RUN_ROOT','.'))/'results/behavior';ss=[json.loads(p.read_text()) for p in (R/'sessions').glob('factorial*.json')];fig,axs=plt.subplots(1,3,figsize=(12,3.5),layout='constrained')
for ax,name in zip(axs,['paper_fig4_mul11','appendix_mcm71931','fir_style_12_41_21']):
 for pool,color in [('initial','gray'),('expanded','tab:green')]:
  for cost,style in [('static',':'),('feedback','-')]:
   s=next(s for s in ss if s['name']==name and s['pool']==pool and s['selection']=='feedback' and s['cost']==cost and s['seed']==0)
   gates=[s['baseline']['gates']]+[json.loads((R/'runs'/f'{i}.json').read_text())['metrics']['gates'] for i in s['records']];best=[min(gates[:i+1]) for i in range(len(gates))]
   ax.plot(range(1,8),best,style,color=color,marker='o',markersize=3,label=f'{pool}/{cost}')
 ax.set_title(name.replace('paper_fig4_','').replace('appendix_',''));ax.set_xlabel('Actual synthesis calls (reference included)');ax.set_ylabel('Best generic gates so far');ax.set_xticks(range(1,8))
axs[0].legend(fontsize=7);fig.suptitle('Native egglog + online synthesis feedback; deterministic controller, W=8');fig.savefig(R/'online_traces.png',dpi=160)
ps=json.loads((R/'online_pareto.json').read_text());fig,axs=plt.subplots(1,3,figsize=(11,3.4),layout='constrained')
for ax,name in zip(axs,['paper_fig4_mul11','appendix_mcm71931','fir_style_12_41_21']):
 rows=[r for r in ps if r['name']==name];ax.scatter([r['depth'] for r in rows],[r['gates'] for r in rows],color='gray',label='verified observed pairs');front=sorted([(r['depth'],r['gates']) for r in rows if r['nondominated']]);ax.plot(*zip(*front),marker='o',color='green',label='nondominated');ax.set_title(name.replace('paper_fig4_','').replace('appendix_',''));ax.set_xlabel('Generic logic depth');ax.set_ylabel('Generic gates')
axs[0].legend(fontsize=7);fig.suptitle('Paired metrics from online factorial only (Figure 4 probes excluded)');fig.savefig(R/'online_pareto.png',dpi=160)
