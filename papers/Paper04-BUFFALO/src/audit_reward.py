#!/usr/bin/env python3
"""Numerical audit of published GRAE definitions, not a policy trainer."""
import json
from pathlib import Path
from pilot import grae
root=Path(__file__).resolve().parents[1]
rows=[{'tns_ps':-30,'buffer_area_um2':1.0,'violations':[]},{'tns_ps':-20,'buffer_area_um2':1.1,'violations':[]},{'tns_ps':-10,'buffer_area_um2':1.2,'violations':['illegal']}]
correct=grae(rows,0);literal=grae(rows,0,literal=True)
zero=[{'tns_ps':0,'buffer_area_um2':1.0,'violations':[]}]*3
r={'interpretation':'Eq.2 area-centered versus literal Algorithm 2 using mean of positive area increases','input':rows,'area_only_corrected_scores':correct,'area_only_literal_scores':literal,'corrected_winner':max(range(3),key=correct.__getitem__),'literal_winner':max(range(3),key=literal.__getitem__),'zero_variance_local_guard_scores':grae(zero,0.5),'paper_zero_variance_rule':'not specified','policy_updates':0}
assert r['corrected_winner']==0 and r['literal_winner']==2
(root/'metrics'/'reward_audit.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
