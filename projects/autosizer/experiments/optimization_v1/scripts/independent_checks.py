"""Audit recorded attempts and exported waveforms without optimizer/scorer imports."""
from pathlib import Path
import csv
import hashlib
import json
import math
import re
import numpy as np
import yaml

EXP=Path(__file__).resolve().parents[1]
PROJECT=EXP.parents[1]
def write(name,value):
    (EXP/'results'/name).write_text(json.dumps(value,indent=2,allow_nan=False))
def number(text,name):
    matches=re.findall(rf'(?m)^\s*{re.escape(name)}\s*=\s*([+-]?[\d.]+(?:e[+-]?\d+)?)',text,re.I)
    return float(matches[-1]) if matches else None
def specs_from_source(circuit):
    cfg=yaml.safe_load((PROJECT/'upstream'/f'{circuit}.yaml').read_text())
    specs={}
    for s in cfg['user_specs_metric'].split(' AND '):
        metric,op,target=re.fullmatch(r'(\w+)\s*([<>])\s*([\d.]+)',s).groups()
        specs[metric]=(op,float(target))
    return cfg,specs
def independent_score(circuit,m):
    _,spec=specs_from_source(circuit)
    if circuit=='inverter':
        fom=(m['dc_gain_db']/spec['dc_gain_db'][1])*spec['average_delay'][1]/m['average_delay']*spec['dynamic_power'][1]/m['dynamic_power']
    else:
        fom=m['dc_gain_db']/spec['dc_gain_db'][1]*m['ugbw']/spec['ugbw'][1]*spec['power_dc'][1]/m['power_dc']
    values=m|{'fom':fom}
    feasible=all(values[k]>v if op=='>' else values[k]<v for k,(op,v) in spec.items())
    return fom,feasible

attempts=[json.loads(p.read_text()) for p in sorted((EXP/'logs/attempts').glob('*/attempt.json'))]
assert len(attempts)==1029
assert [r['global_attempt'] for r in attempts]==list(range(1,1030))
issues=[]
for row in attempts:
    folder=Path(row['cwd'])
    assert hashlib.sha256((folder/'circuit.spice').read_bytes()).hexdigest()==row['deck_sha256']
    assert (folder/'stdout.log').is_file() and (folder/'stderr.log').is_file()
    if not row['measurement_valid']:
        assert row['normalized_fom'] is None
        continue
    cfg,_=specs_from_source(row['circuit'])
    text=(folder/'stdout.log').read_text()
    measured={}
    for metric in cfg['metrics']:
        if metric=='fom':continue
        source='dynamic_power_timeweighted' if metric=='dynamic_power' and row['mode']=='corrected' else metric
        raw=number(text,source)
        assert raw is not None
        measured[metric]=raw*float(cfg['metric_post'][metric].get('scale',1))
    fom,feasible=independent_score(row['circuit'],measured)
    assert math.isclose(fom,row['normalized_fom'],rel_tol=1e-12,abs_tol=1e-12)
    assert feasible==row['feasible']

summaries=json.loads((EXP/'results/main_summaries.json').read_text())
for s in summaries:
    h=json.loads((EXP/'results/main'/s['run']/'history.json').read_text())
    decisions=json.loads((EXP/'results/main'/s['run']/'decisions.json').read_text())
    assert len(h)==36 and len({tuple(r['indices']) for r in h})==36
    for i,(r,d) in enumerate(zip(h,decisions)):
        assert r['indices']==d['indices'] and r['context']['within_run']==i+1
        assert all(lo<=index<=hi for index,(lo,hi) in zip(r['indices'],d['bounds']))
        if d['detail']['engine']=='GP_UCB':
            assert d['detail']['training_valid_observations']==sum(x['measurement_valid'] for x in h[:i])
    for other in summaries:
        if other['circuit']==s['circuit'] and other['seed']==s['seed']:
            assert other['initialization']==s['initialization']
assert max(r['global_attempt'] for r in attempts if r['context']['stage']=='main') < min(r['global_attempt'] for r in attempts if r['context']['stage']=='heldout_oracle')

def crossings(t,y,rising):
    mask=(y[:-1]<.9)&(y[1:]>=.9) if rising else (y[:-1]>.9)&(y[1:]<=.9)
    return [float(t[i]+(.9-y[i])*(t[i+1]-t[i])/(y[i+1]-y[i])) for i in np.flatnonzero(mask)]

waveforms=[]
validation=json.loads((EXP/'results/validation.json').read_text())
for item in validation:
    row=item['refined'];folder=Path(row['cwd'])
    check={'run':item['run'],'validation_attempt':row['global_attempt'],'source_measurements':row['metrics']}
    if not row['measurement_valid']:
        check['status']='measurement_invalid_no_imputation';waveforms.append(check);continue
    if row['circuit']=='inverter':
        t,vin,vout,power=np.loadtxt(folder/'tran.tsv',skiprows=1).T
        ir,inf=crossings(t,vin,True)[0],crossings(t,vin,False)[0]
        of=next(x for x in crossings(t,vout,False) if x>=ir)
        ora=next(x for x in crossings(t,vout,True) if x>=inf)
        delay=((of-ir)+(ora-inf))*.5e12
        dynamic=abs(float(np.trapezoid(power,t)/(t[-1]-t[0]))-row['extra_raw_metrics']['static_power_abs'])*1e6
        dc=np.loadtxt(folder/'dc.tsv',skiprows=1)
        gain=float(20*np.log10(max(abs(np.gradient(dc[:,2],dc[:,1])))))
        measured={'dc_gain_db':gain,'average_delay':delay,'dynamic_power':dynamic}
        # Printed SPICE measurements have about seven significant figures.
        assert abs(delay-row['metrics']['average_delay'])<.001
        assert abs(dynamic-row['metrics']['dynamic_power'])<.001
        assert abs(gain-row['metrics']['dc_gain_db'])<.001
    else:
        data=np.loadtxt(folder/'ac.tsv',skiprows=1);f,mag=data[:,0],data[:,1]
        db=20*np.log10(mag);index=int(np.flatnonzero((db[:-1]>0)&(db[1:]<=0))[0])
        unity=float((f[index]-db[index]*(f[index+1]-f[index])/(db[index+1]-db[index]))*1e-6)
        stdout=(folder/'stdout.log').read_text()
        current=number(stdout,'i(vdd)')
        assert current is not None
        measured={'dc_gain_db':float(db[0]),'ugbw':unity,'power_dc':abs(current)*1.8e6}
        assert abs(unity-row['metrics']['ugbw'])<.001
        assert abs(measured['dc_gain_db']-row['metrics']['dc_gain_db'])<.001
        assert abs(measured['power_dc']-row['metrics']['power_dc'])<.001
    fom,feasible=independent_score(row['circuit'],measured)
    check.update(independent_measurements=measured,independent_fom=fom,independent_feasible=feasible,
                 parsed_refined_feasible=row['feasible'],original_measurement_feasible=item['original']['feasible'])
    if feasible!=row['feasible']:issues.append({'run':item['run'],'reason':'independent feasibility differs at displayed precision'})
    waveforms.append(check)
write('independent_waveform_checks.json',waveforms)
write('correctness_checks.json',{'attempts_recomputed':len(attempts),'all_deck_hashes_verified':True,
      'strict_individual_constraints_recomputed':True,'all_main_budgets_and_unique_points':True,
      'shared_initialization':True,'GP_training_uses_past_valid_measurements_only':True,
      'oracle_after_search_no_feedback':True,'waveform_remeasurements':len(waveforms),'precision_edge_cases':issues})
print(f'{len(attempts)} recorded attempts independently rescored; {len(waveforms)} winner waveforms checked; {len(issues)} precision edge cases.')
