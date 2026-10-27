"""Posthoc only: observed cross-stage rank reversals and pruned-parent coverage.
Never called by search. Unobserved configurations are never assigned oracle QoR.
"""
import json,itertools,math,collections
from eda import ROOT,PLACE
from qor import logic,layout
R=ROOT/'results';summaries=[json.loads(p.read_text()) for p in R.glob('*.summary.json')];records=[json.loads(l) for p in R.glob('*.jsonl') for l in p.read_text().splitlines()];output={}
for design in ('adder_32bit','multi_pipe_8bit','barrel_shifter','div_16bit'):
 ss=[s for s in summaries if s['design']==design and 'probe' not in s['run']];ref=ss[0]['reference'];rr=[r for r in records if r['design']==design and r['status']=='ok' and not r['run'].startswith('pilot')]
 parents=[]
 for synth in sorted({r['s'] for r in rr if r['stage']=='synth'}):
  a=next(r for r in rr if r['stage']=='synth' and r['s']==synth);children=[r for r in rr if r['stage']=='place' and r['s']==synth]
  if not children:continue
  best=min(children,key=lambda r:layout(r['area'],r['power'],r['slack'],ref))
  parents.append({'s':synth,'synth_qor':logic(a['area'],a['power'],a['slack'],ref),'synth_area':a['area'],'synth_slack':a['slack'],'observed_best_placed_qor':layout(best['area'],best['power'],best['slack'],ref),'observed_p_count':len({r['p'] for r in children}),'p_space_size':len(PLACE),'placed_slack_range':[min(r['slack'] for r in children),max(r['slack'] for r in children)],'timing_feasible_children':sum(r['slack']>=0 for r in children),'best_config':[best['s'],best['p']]})
 reversals=[]
 for a,b in itertools.permutations(parents,2):
  if a['synth_qor']<b['synth_qor']-1e-12 and a['observed_best_placed_qor']>b['observed_best_placed_qor']+1e-12:reversals.append({'earlier_better_s':a['s'],'later_better_s':b['s'],'earlier_qor':[a['synth_qor'],b['synth_qor']],'later_best_observed_qor':[a['observed_best_placed_qor'],b['observed_best_placed_qor']]})
 probe=[]
 for su in [s for s in summaries if s['design']==design]:
  for e in su['events']:
   if e['event']=='prune':
    parent=next(p for p in parents if p['s']==e['s']);probe.append(dict(e,run=su['run'],later_observed_best=parent['observed_best_placed_qor'],later_coverage=parent['observed_p_count'],could_beat_event_baseline=parent['observed_best_placed_qor']<e['baseline']))
 output[design]={'parents':parents,'strict_rank_reversals':reversals,'pruning_events_posthoc':probe,'limits':'Parents have varying observed p coverage. Best-observed values are not full-space optima. Posthoc observations never enter serving database or optimizer.'}
(R/'cross_stage_audit.json').write_text(json.dumps(output,indent=2))
lines=['# Observed cross-stage evidence','', '| Design | Parents with placed descendants | Strict QoR ranking reversals | Pruning events |','|---|---:|---:|---:|']
for d,x in output.items():lines.append(f'| {d} | {len(x["parents"])} | {len(x["strict_rank_reversals"])} | {len(x["pruning_events_posthoc"])} |')
lines+=['','The downstream categorical parameter domain is shared across parents. Upstream netlists change mapped cells/area and the physical geometry used by placement. This experiment does not demonstrate a change in which parameter values are legal. Timing feasibility is evaluated from actual placed slack, not inferred from structural similarity.','', 'Strict reversals exclude ties. Different child coverage means this is an observed mechanism audit, not an oracle optimal-parent ranking. Early-prune loss is evaluated only when independent later observations exist and remains coverage-limited.']
(R/'cross_stage_summary.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
