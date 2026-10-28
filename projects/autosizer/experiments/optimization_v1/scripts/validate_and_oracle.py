"""Post-search winner remeasurement, then a strictly held-out inverter grid."""
import itertools
import json
from engine import EXP,CONFIG,evaluate,save

summaries=json.loads((EXP/'results/main_summaries.json').read_text())
assert len(summaries)==24 and all(s['attempts']==36 for s in summaries)
if (EXP/'results/validation.json').exists() or (EXP/'results/oracle.json').exists():
    raise RuntimeError('Never overwrite/reselect completed independent measurements')
validations=[]
for summary in summaries:
    assert summary['selected_indices'] is not None
    selection={'selected_run':summary['run'],'selected_global_attempt':summary['selected_global_attempt'],
               'original_selection_feasible':summary['selected_is_feasible']}
    original=evaluate(summary['circuit'],summary['selected_indices'],
                      {'stage':'validation_original',**selection},mode='original')
    refined=evaluate(summary['circuit'],summary['selected_indices'],
                     {'stage':'validation_refined_export',**selection},mode='corrected',export=True,refined=True)
    validations.append({'run':summary['run'],'original':original,'refined':refined})
    save(EXP/'results/validation_partial.json',validations)
save(EXP/'results/validation.json',validations)
print('24 preselected winners remeasured twice; no winner replacement.',flush=True)
oracle=[]
for point in itertools.product(range(9),repeat=2):
    oracle.append(evaluate('inverter',list(point),{'stage':'heldout_oracle','not_fed_to_search':True},mode='corrected'))
    save(EXP/'results/oracle_partial.json',oracle)
save(EXP/'results/oracle.json',oracle)
feasible=[r for r in oracle if r['status']=='valid_feasible']
best=max(feasible,key=lambda r:r['normalized_fom']) if feasible else None
save(EXP/'results/oracle_summary.json',{'points':len(oracle),'valid':sum(r['measurement_valid'] for r in oracle),
     'feasible_points':len(feasible),'best_indices':best['indices'] if best else None,
     'best_feasible_fom':best['normalized_fom'] if best else None,'domain':'released discrete inverter grid only',
     'fed_to_search':False,'global_attempt_range':[oracle[0]['global_attempt'],oracle[-1]['global_attempt']]})
print('81-point held-out inverter grid complete.',flush=True)
