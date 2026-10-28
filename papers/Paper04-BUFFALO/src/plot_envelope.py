#!/usr/bin/env python3
"""Plot corrected-load, same-implementation area-delay outcomes only."""
import json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pilot import ROOT
s=json.loads((ROOT/'metrics'/'envelope.json').read_text())
cols=['net','configuration','output_load_ff','buffer_area','max_arrival_ps','tns_ps','status','nondominated_within_panel','sta_wall_seconds']
with (ROOT/'metrics'/'envelope.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(s['rows'])
fig,axes=plt.subplots(1,3,figsize=(12,3.8),layout='constrained')
for ax,net in zip(axes,['clustered','spread','aes_cut']):
 rows=[r for r in s['rows'] if r['net']==net and r['output_load_ff']==1.44]
 for r in rows:
  label=('x4f @10%' if 'x4f' in r['configuration'] else ('x8 @25%' if '25pct' in r['configuration'] else 'x8 @10%'))
  ax.scatter(r['buffer_area'],r['max_arrival_ps'],marker='o' if r['nondominated_within_panel'] else 'x',s=60)
  ax.annotate(label,(r['buffer_area'],r['max_arrival_ps']),xytext=((-4,4) if r['buffer_area']>.5 else (3,4)),ha=('right' if r['buffer_area']>.5 else 'left'),textcoords='offset points',fontsize=8)
 front=sorted([r for r in rows if r['nondominated_within_panel']],key=lambda r:r['buffer_area'])
 ax.plot([r['buffer_area'] for r in front],[r['max_arrival_ps'] for r in front],color='gray',alpha=.6)
 ax.axhline(80,ls='--',color='red',lw=1);ax.set(title=net,xlabel='Inserted buffer area (library units)',ylabel='Same-implementation worst arrival (ps)',ylim=(70,180));ax.grid(alpha=.2);ax.margins(x=.25)
fig.suptitle('Local feasibility envelope • endpoint load1.44fF • actual target remains80ps\nPanel nondominance only; no LLM, RL, physical closure or paper-performance claim',fontsize=11)
fig.savefig(ROOT/'figures'/'feasibility_envelope.png',dpi=170)
print('Wrote corrected-load Pareto figure and12-row CSV; no STA calls.')
