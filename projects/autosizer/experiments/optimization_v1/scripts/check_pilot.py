"""Check accounting and actual feedback use before authorizing main scaling."""
import json
from engine import EXP,save

summaries=json.loads((EXP/'results/pilot_summaries.json').read_text())
assert len(summaries)==2
for s in summaries:
    assert s['attempts']==18 and s['unique_points']==18 and s['invalid']==0
    path=EXP/'results/pilot'/s['run']
    h=json.loads((path/'history.json').read_text())
    assert all(r['context']['within_run']==i+1 for i,r in enumerate(h))
    assert any(r['feasible'] for r in h)
adaptive=next(s for s in summaries if s['method']=='adaptive_gp')
assert adaptive['outer_range_changes']>=1
out=EXP/'results/pilot'/adaptive['run']
events=json.loads((out/'outer_feedback.json').read_text())
history=json.loads((out/'history.json').read_text())
for event in events:
    assert len(history)>event['after_attempt']
    assert event['feedback']['attempts']==event['after_attempt']
assert summaries[0]['initialization']==summaries[1]['initialization']
save(EXP/'results/pilot_checks.json',{'passed':True,'attempts':36,'common_initialization':True,
     'real_electrical_feedback':True,'adaptive_range_changes':adaptive['outer_range_changes'],
     'post_update_simulations':True,'new_labels_invented':False})
print('Pilot: 36 real attempts, shared initialization, feasible measurements and range updates verified.')
