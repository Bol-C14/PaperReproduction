"""Bounded offline audit of pinned upstream metric parsers; no model calls.
Usage: python evaluator_controls.py /path/to/official/OpenLayout out.json
No benchmark reference answers are copied into this public script.
"""
import json,sys,tempfile,importlib.util
from pathlib import Path
root=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root))
from openlayout.metrics import parse_log_metrics,count_drc_violations,extract_errors
from openlayout.agents import goal_check,score_metrics
cases={
 'well_formed':'worst slack max -0.25\nworst slack min 0.05\nNumber of violations = 9\n',
 'empty':'',
 'pass_only':'PASS\n',
 'keyword_forgery':'This is not a routed result.\nworst slack max 0.10\nNumber of violations = 0\n',
 'later_spoof':'worst slack max -0.25\nNumber of violations = 9\nUNTRUSTED ECHO: worst slack max 0.10\nUNTRUSTED ECHO: Number of violations = 0\n',
 'fatal_with_metrics':'[ERROR DRT-0001] route failed\nworst slack max 0.10\nNumber of violations = 0\n',
 'hold_missing':'worst slack max 0.10\nNumber of violations = 0\n',
 'hold_negative':'worst slack max 0.10\nworst slack min -0.05\nNumber of violations = 0\n',
}
out={'kind':'offline_replay','not_a_model_or_task_correctness_score':True,'cases':[]}
for name,text in cases.items():
 metrics=parse_log_metrics(text);ok,fail=goal_check(metrics,{})
 out['cases'].append({'case':name,'raw_input':text,'parsed':metrics,'goal_check':ok,'failures':fail,'errors':extract_errors(text),'score':score_metrics(metrics)})
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'drc.rpt';p.write_text('FATAL: detailed routing aborted; no report generated\n')
 out['malformed_existing_drc_report']={'raw_input':p.read_text(),'count':count_drc_violations(p),'missing_file_count':count_drc_violations(Path(td)/'missing')}
Path(sys.argv[2]).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
