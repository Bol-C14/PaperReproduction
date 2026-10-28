#!/usr/bin/env python3
"""Offline, stdlib-only recheck of raw STA outputs and serialized trees."""
import json
import math
from pathlib import Path
import re
from pilot import ROOT, decode, encode, flatten, fixture, library, validate
_,lib=library();count=0
for metric in ['pilot.json','aes_pilot.json']:
    data=json.loads((ROOT/'metrics'/metric).read_text())
    for r in data['rows']:
        out=ROOT/'runs'/r['net']/f"{r['method']}-{r['index']}"
        f=fixture(r['net']);fixed={n['id']:n for n in [f['driver']]+f['sinks']}
        seq=json.loads((out/'sequence.json').read_text());tree=decode(seq,fixed)
        assert encode(tree)==seq
        assert json.loads((out/'decoded_tree.json').read_text())==tree
        nodes=flatten(tree);assert len({n['id'] for n in nodes})==len(nodes)
        assert sum(len(n.get('children',[])) for n in nodes)==len(nodes)-1
        queries=[x for x in (out/'sta.conf').read_text().splitlines() if x.startswith(('report_at ','report_slew '))]
        vals=[float(x) for x in (out/'stdout.txt').read_text().splitlines() if re.fullmatch(r'\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\s*',x)]
        assert len(queries)==len(vals) and all(map(math.isfinite,vals))
        arrivals=[v for q,v in zip(queries,vals) if q.startswith('report_at')]
        slews=[v for q,v in zip(queries,vals) if q.startswith('report_slew')]
        ep=[max(arrivals[i:i+2]) for i in range(0,len(arrivals),2)]
        assert len(ep)==len(f['sinks'])
        assert abs(sum(min(0,f['required_ps']-x) for x in ep)-r['tns_ps'])<1e-7
        assert abs(min(0,f['required_ps']-max(ep))-r['wns_ps'])<1e-7
        assert abs(max(slews)-r['max_slew_ps'])<1e-7
        assert abs(sum(lib[n['cell']]['area'] for n in nodes if n['id'].startswith('B'))-r['buffer_area_um2'])<1e-7
        violations=validate(tree,f,lib)
        if max(slews)>f['max_slew_ps']:violations.append('max_transition')
        assert sorted(set(violations))==r['violations']
        assert '\nE ' not in (out/'engine.log').read_text()
        assert not (out/'stderr.txt').read_text()
        count+=1
print(json.dumps({'raw_sta_cases_recomputed':count,'tree_roundtrips':count,'rooted_connected_acyclic_unique_id_checks':count,'constraint_outcomes_recomputed':count,'result':'PASS'},indent=2))
