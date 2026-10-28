#!/usr/bin/env python3
"""Recompute descriptive summaries/figures from archived actual-STA results."""
import csv
import json
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
allrows=[]
for filename in ['pilot.json','aes_pilot.json']:
    allrows+=json.loads((ROOT/'metrics'/filename).read_text())['rows']
cols=['net','method','index','tns_ps','wns_ps','max_arrival_ps','max_slew_ps','buffer_area_um2','buffer_count','wirelength_um','sta_wall_seconds','violations']
with (ROOT/'metrics'/'candidates.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(allrows)
summary=[]
curves=[]
for net in ['clustered','spread','aes_cut']:
    for method in ['unbuffered','geometric','random']:
        rows=[r for r in allrows if r['net']==net and r['method']==method]
        legal=[r for r in rows if not r['violations']]
        best=max(legal,key=lambda r:r['tns_ps']) if legal else max(rows,key=lambda r:r['tns_ps'])
        summary.append({'net':net,'method':method,'attempts':len(rows),'sta_calls':len(rows),'valid':len(legal),'best_tns_ps':best['tns_ps'],'best_wns_ps':best['wns_ps'],'best_area':best['buffer_area_um2'],'best_index':best['index'],'selection':'timing-only, among legal candidates; invalid anchor shown separately','sum_sta_seconds':sum(r['sta_wall_seconds'] for r in rows)})
        if method!='unbuffered':
            for n in [1,2,4,8]:
                curves.append({'net':net,'method':method,'budget':n,'best_tns_ps':max(r['tns_ps'] for r in rows[:n] if not r['violations'])})
(ROOT/'metrics'/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(ROOT/'metrics'/'budget_curves.json').write_text(json.dumps(curves,indent=2)+'\n')
fig,axes=plt.subplots(1,3,figsize=(12,3.7),layout='constrained')
for ax,net in zip(axes,['clustered','spread','aes_cut']):
    for method,color in [('geometric','#216e39'),('random','#9467bd')]:
        rows=[r for r in allrows if r['net']==net and r['method']==method]
        ax.scatter([r['buffer_area_um2'] for r in rows],[-r['tns_ps'] for r in rows],label=method,color=color)
        front=[r for r in rows if not any(q['buffer_area_um2']<=r['buffer_area_um2'] and q['tns_ps']>=r['tns_ps'] and (q['buffer_area_um2']<r['buffer_area_um2'] or q['tns_ps']>r['tns_ps']) for q in rows)]
        front.sort(key=lambda r:r['buffer_area_um2']);ax.plot([r['buffer_area_um2'] for r in front],[-r['tns_ps'] for r in front],color=color,alpha=.5)
    ax.set(title=net,xlabel='Inserted buffer area (library units)',ylabel='Negative slack magnitude sum (ps)');ax.grid(alpha=.2)
axes[0].legend();fig.suptitle('Actual OpenTimer STA • 8 candidates/method/net • no model training');fig.savefig(ROOT/'figures'/'area_timing.png',dpi=170);plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(12,3.7),layout='constrained')
for ax,net in zip(axes,['clustered','spread','aes_cut']):
    for method in ['geometric','random']:
        rows=[r for r in curves if r['net']==net and r['method']==method]
        ax.plot([r['budget'] for r in rows],[-r['best_tns_ps'] for r in rows],marker='o',label=method)
    ax.set(title=net,xlabel='Actual STA candidate budget',ylabel='Best negative slack magnitude (ps)',xticks=[1,2,4,8]);ax.grid(alpha=.2)
axes[0].legend();fig.suptitle('Best-of-N selection gains without learning • order-dependent descriptive pilot');fig.savefig(ROOT/'figures'/'budget.png',dpi=170);plt.close(fig)
# One actual AES-cut tree, no implication of physical legalization.
example=json.loads((ROOT/'runs'/'aes_cut'/'geometric-3'/'decoded_tree.json').read_text())
fig,ax=plt.subplots(figsize=(5,5),layout='constrained')
def draw(n):
    c='tab:red' if n['id']=='D' else ('tab:blue' if n['id'].startswith('L') else 'tab:green')
    ax.scatter(n['x'],n['y'],c=c,s=24);ax.annotate(n['id'],(n['x'],n['y']),fontsize=7)
    for ch in n.get('children',[]):
        ax.plot([n['x'],ch['x'],ch['x']],[n['y'],n['y'],ch['y']],color='gray',lw=.6);draw(ch)
draw(example);ax.set(xlim=(-5,105),ylim=(-5,105),xlabel='Assumed x (um)',ylabel='Assumed y (um)',title='AES net cut • assumed placement\nLogical tree only; no legalization/routing');fig.savefig(ROOT/'figures'/'aes_tree.png',dpi=170)
print(json.dumps({'comparison_sta_calls':len(allrows),'sta_wall_seconds':sum(r['sta_wall_seconds'] for r in allrows),'all_buffered_candidates_valid':all(not r['violations'] for r in allrows if r['method']!='unbuffered'),'timing_closed_buffered_candidates':sum(r['tns_ps']==0 for r in allrows if r['method']!='unbuffered')},indent=2))
