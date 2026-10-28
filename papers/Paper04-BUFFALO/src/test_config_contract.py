#!/usr/bin/env python3
"""SDC/score configuration contract test; no STA or sweep.
Checks nondefault constraints and byte-for-byte preservation of all 51 archived
comparison netlist/SDC/SPEF inputs under their original default configurations.
"""
import copy
import json
from pathlib import Path
import re
import tempfile
from pilot import ROOT, decode, emit, fixture, library, timing_metrics, validate

_,lib=library()
f=fixture('clustered')
f.update(period_ps=137.5,required_ps=96.25,input_delay_ps=7.25,
         input_slew_ps=13.75,output_load_ff=1.25,max_fanout=2)
tree=dict(f['driver'],children=f['sinks'])
with tempfile.TemporaryDirectory(prefix='buffalo-config-',dir='/tmp') as directory:
    out=Path(directory)
    emit(tree,f,out,ROOT/'vendor'/'asap7.lib')
    sdc=(out/'tree.sdc').read_text()
    period=float(re.search(r'create_clock -period ([\d.]+)',sdc).group(1))
    delays=[float(x) for x in re.findall(r'set_output_delay ([\d.]+)',sdc)]
    assert len(delays)==2*len(f['sinks']) and set(delays)=={41.25}
    emitted_required=period-delays[0]
    assert emitted_required==f['required_ps']
    assert set(re.findall(r'set_input_delay ([\d.]+)',sdc))=={'7.25'}
    assert set(re.findall(r'set_input_transition ([\d.]+)',sdc))=={'13.75'}
    assert set(re.findall(r'set_load -pin_load ([\d.]+)',sdc))=={'1.25'}
    arrivals=[f['required_ps']+12.5,f['required_ps']+2.5]+[f['required_ps']-4]*22
    score=timing_metrics(arrivals,f)
    expected=sum(min(0,emitted_required-max(arrivals[i:i+2])) for i in range(0,len(arrivals),2))
    assert score['tns_ps']==expected==-12.5 and score['wns_ps']==-12.5
    assert 'max_fanout' in validate(tree,f,lib)
    f['max_fanout']=12
    assert 'max_fanout' not in validate(tree,f,lib)
    f['max_fanout']=11
    assert 'max_fanout' in validate(tree,f,lib)
    verified=0
    for metric in ['pilot.json','aes_pilot.json']:
        for row in json.loads((ROOT/'metrics'/metric).read_text())['rows']:
            case=fixture(row['net'])
            raw=ROOT/'runs'/row['net']/f"{row['method']}-{row['index']}"
            fixed={n['id']:n for n in [case['driver']]+case['sinks']}
            candidate=decode(json.loads((raw/'sequence.json').read_text()),fixed)
            emit(candidate,case,out,ROOT/'vendor'/'asap7.lib')
            for name in ['tree.v','tree.sdc','tree.spef']:
                assert (out/name).read_bytes()==(raw/name).read_bytes(),(row['net'],row['method'],row['index'],name)
            verified+=1
result={'result':'PASS','nondefault':{'period_ps':137.5,'required_ps':96.25,
        'input_delay_ps':7.25,'input_slew_ps':13.75,'output_load_ff':1.25},
        'output_delay_ps':41.25,'score_tns_ps':-12.5,'score_wns_ps':-12.5,
        'fanout_thresholds_checked':[2,12,11],
        'default_cases_byte_identical':verified,'default_input_files_byte_identical':3*verified,
        'actual_sta_calls_added':0,'input_pin_slew_observed':False}
print(json.dumps(result,indent=2))
