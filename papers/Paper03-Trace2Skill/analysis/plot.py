#!/usr/bin/env python3
import csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parents[1]
r=list(csv.DictReader((P/'metrics/task_results.csv').open()));tasks=[x['task'].removeprefix('cvdp_agentic_heavy_') for x in r if x['condition']=='C3'];colors={'C3':'#2367A1','C4':'#C57420'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(10,5.8))
for c,off in [('C3',-.18),('C4',.18)]:
 a=[x for x in r if x['condition']==c];y=[i+off for i in range(8)];v=[int(x['passes']) for x in a]
 bars=ax.barh(y,v,height=.33,label=c,color=colors[c],hatch='//' if c=='C4' else None)
 for b,k in zip(bars,v):ax.text(k+.7,b.get_y()+b.get_height()/2,f'{k}/80',va='center',fontsize=10)
ax.set_yticks(range(8),tasks);ax.invert_yaxis();ax.set_xlim(0,94);ax.set_xlabel('Passing optimization rollouts (80 per task/condition)');ax.set_title('Task-local cached outcomes: heterogeneous C4 gains');ax.legend(loc='lower right');ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
fig.text(.02,.015,'Public sanitized records, commit 5702b3f. Adaptive optimization attempts; no frozen-skill held-out test.',fontsize=9);fig.tight_layout(rect=(0,.035,1,1));fig.savefig(P/'figures/task_outcomes.png',dpi=180);fig.savefig(P/'figures/task_outcomes.svg');plt.close(fig)
g=list(csv.DictReader((P/'metrics/generation_results.csv').open()));fig,axes=plt.subplots(1,2,figsize=(10,4.6))
for c in ['C3','C4']:
 a=[x for x in g if x['condition']==c];x=[int(z['generation']) for z in a]
 axes[0].plot(x,[int(z['passes'])/128*100 for z in a],marker='o' if c=='C3' else 's',color=colors[c],label=c)
 axes[1].plot(x,[int(z['valid']) for z in a],marker='o' if c=='C3' else 's',color=colors[c],label=c)
for ax in axes:ax.set_xticks(range(1,6));ax.set_xlabel('Generation');ax.grid(alpha=.15);ax.legend()
axes[0].set_ylabel('Pass rate (%) over all 128 attempts');axes[0].set_ylim(0,45);axes[0].set_title('All attempts retained in denominator')
axes[1].set_ylabel('Valid, unblocked candidates (out of 32)');axes[1].set_ylim(0,34);axes[1].set_title('Quality-plot eligible population shrinks')
fig.text(.02,.015,'Generation 1 includes seed plus three initial mutants; curves are descriptive, not independent replications.',fontsize=9);fig.tight_layout(rect=(0,.035,1,1));fig.savefig(P/'figures/generation_audit.png',dpi=180);fig.savefig(P/'figures/generation_audit.svg');plt.close(fig)

# Normalize renderer whitespace in authored SVGs; never change vendored source.
for f in (P/'figures').glob('*.svg'):
 f.write_text('\n'.join(x.rstrip() for x in f.read_text().splitlines())+'\n')
