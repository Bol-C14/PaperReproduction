import json,os
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parents[1]/Path(os.environ.get('ASPEN_ATTRIBUTION_RUN_ROOT','.'))/'results/attribution_round'
rows=json.loads((O/'comparison_summary.json').read_text());fig,axs=plt.subplots(1,2,figsize=(10,3.6),layout='constrained')
for ax,name in zip(axs,['appendix_mcm71931','mcm593']):
 ss=[s for s in rows if s['fixture']==name]
 for s in ss:
  ax.plot(range(1,7),[v['gates'] for v in s['observed_paired_metrics']],marker='o',label=s['policy'])
 ax.set_title(f"{name}, W={ss[0]['width']}");ax.set_xlabel('Actual synthesis query (six unique RTL per arm)');ax.set_ylabel('Observed generic gate count');ax.set_xticks(range(1,7))
axs[0].legend(fontsize=8);fig.suptitle('Bounded cost/attribution substitute: differing trajectories, no stable numerical advantage');fig.savefig(O/'comparison_trajectories.png',dpi=160)
