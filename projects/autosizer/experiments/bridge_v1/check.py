"""Independent raw-log and waveform audit: no optimizer/scorer/controller imports."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import numpy as np
import yaml

PROJECT=Path(__file__).resolve().parents[2]

def save(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def independent_metrics(row,folder):
    text=(folder/'stdout.log').read_text()
    def number(name):
        found=re.findall(rf'(?mi)^\s*{re.escape(name)}\s*=\s*([+-]?[\d.]+(?:e[+-]?\d+)?)',text)
        if not found:raise ValueError('Missing independent raw metric: '+name)
        return float(found[-1])
    power='dynamic_power_timeweighted' if row['mode']=='corrected' else 'dynamic_power'
    return {'dc_gain_db':number('dc_gain_db'),'average_delay':number('average_delay')*1e12,
            'dynamic_power':number(power)*1e6}

def rescore(metrics):
    cfg=yaml.safe_load((PROJECT/'upstream/inverter.yaml').read_text())
    specs={}
    for clause in cfg['user_specs_metric'].split(' AND '):
        name,op,value=re.fullmatch(r'(\w+)\s*([<>])\s*([\d.]+)',clause).groups()
        specs[name]=(op,float(value))
    fom=metrics['dc_gain_db']/specs['dc_gain_db'][1]*specs['average_delay'][1]/metrics['average_delay']*specs['dynamic_power'][1]/metrics['dynamic_power']
    values=metrics|{'fom':fom}
    feasible=all(values[k]>limit if op=='>' else values[k]<limit for k,(op,limit) in specs.items())
    return fom,feasible

def waveforms(row,folder):
    t,vin,vout,power=np.loadtxt(folder/'tran.tsv',skiprows=1).T
    def crossings(y,rising):
        flags=(y[:-1]<.9)&(y[1:]>=.9) if rising else (y[:-1]>.9)&(y[1:]<=.9)
        return [float(t[i]+(.9-y[i])*(t[i+1]-t[i])/(y[i+1]-y[i])) for i in np.flatnonzero(flags)]
    ir,inf=crossings(vin,True)[0],crossings(vin,False)[0]
    of=next(x for x in crossings(vout,False) if x>=ir)
    ora=next(x for x in crossings(vout,True) if x>=inf)
    delay=((of-ir)+(ora-inf))*.5e12
    dynamic=abs(float(np.trapezoid(power,t)/(t[-1]-t[0]))-row['extras']['static_power_abs'])*1e6
    dc=np.loadtxt(folder/'dc.tsv',skiprows=1)
    gain=float(20*np.log10(max(abs(np.gradient(dc[:,2],dc[:,1])))))
    measured={'dc_gain_db':gain,'average_delay':delay,'dynamic_power':dynamic}
    for k,v in measured.items():
        if abs(v-row['metrics'][k])>=.001:raise ValueError('Waveform mismatch: '+k)
    fom,feasible=rescore(measured)
    if feasible!=row['feasible']:raise ValueError('Independent waveform feasibility mismatch')
    return {'attempt':row['attempt'],'metrics':measured,'normalized_fom':fom,'feasible':feasible}

def audit(root,preflight=False):
    folders=sorted((root/'attempts').glob('[0-9]*'))
    rows=[json.loads((p/'attempt.json').read_text()) for p in folders]
    assert [r['attempt'] for r in rows]==list(range(1,len(rows)+1))
    assert len(rows)<=56
    checks=[]
    for row,folder in zip(rows,folders):
        assert hashlib.sha256((folder/'circuit.spice').read_bytes()).hexdigest()==row['deck_sha256']
        assert row['status']!='launch_pending'
        assert row['affinity']==list(range(24,32))
        assert (folder/'stderr.log').is_file()
        if row['measurement_valid']:
            m=independent_metrics(row,folder)
            assert m==row['metrics']
            fom,feasible=rescore(m)
            assert math.isclose(fom,row['normalized_fom'],rel_tol=1e-12)
            assert feasible==row['feasible']
            if row['mode']=='corrected' and row['export']:
                checks.append(waveforms(row,folder))
        else:
            assert row['normalized_fom'] is None and not row['feasible']
    if preflight:
        assert len(rows)==3 and len(checks)==2
    else:
        assert len(rows)==53
        for arm in ('test_controller','gp_control'):
            history=json.loads((root/arm/'history.json').read_text())
            assert len(history)==24 and len({tuple(r['indices']) for r in history})==24
            assert all(r['arm']==arm for r in history)
            for i,r in enumerate(history):
                if r['proposal_detail']['engine']=='GP_UCB':
                    assert r['proposal_detail']['training_valid_observations']==sum(x['measurement_valid'] for x in history[:i])
        call_dirs=sorted((root/'test_controller').glob('call_*'))
        assert len(call_dirs)==5
        outer=next(p for p in call_dirs if p.name.endswith('outer_regeneration'))
        req=json.loads((outer/'request.json').read_text())
        context=json.loads(req['messages'][-1]['content'])['context']
        h=json.loads((root/'test_controller/history.json').read_text())
        assert [r['attempt'] for r in context['history']]==[r['attempt'] for r in h[:12]]
        assert context['feedback']['attempts']==12
        assert not any(r['arm']=='gp_control' for r in rows if r['attempt'] in [x['attempt'] for x in context['history']])
        assert json.loads((root/'test_controller/summary.json').read_text())['domain_changed']
        assert len(checks)==4
    report={'passed':True,'attempts':len(rows),'independent_waveform_checks':checks,
            'valid':sum(r['measurement_valid'] for r in rows),'invalid':sum(not r['measurement_valid'] for r in rows),
            'api_calls':0,'backend':'TEST_CONTROLLER_NOT_LLM',
            'all_raw_logs_and_deck_hashes_checked':True,'strict_source_constraints_rescored':True,
            'no_legacy_observations_or_control_feedback':True,
            'limitations':'One easy inverter/seed; deterministic test controller; integration only, not model capability or paper reproduction.'}
    save(root/('preflight_checks.json' if preflight else 'checks.json'),report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('root',type=Path)
    parser.add_argument('--preflight',action='store_true')
    args=parser.parse_args()
    audit(args.root,args.preflight)
