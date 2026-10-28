"""Read-only targeted checks on four existing exports; no new experiment."""
from pathlib import Path
import json
import numpy as np
from plan import independent_parse,independent_score,PROJECT

ROOT=PROJECT/'experiments/bridge_v1/evidence/run_01'

def integral_mean(t,y,start,end):
    if not t[0]<=start<end<=t[-1]:raise ValueError('Integration interval outside vectors')
    inside=(t>start)&(t<end)
    x=np.r_[start,t[inside],end]
    v=np.r_[np.interp(start,t,y),y[inside],np.interp(end,t,y)]
    return float(np.trapezoid(v,x)/(end-start))

def review():
    output=[]
    for number in (1,2,3,52):
        folder=ROOT/'attempts'/f'{number:03d}'
        row=json.loads((folder/'attempt.json').read_text())
        metrics=independent_parse((folder/'stdout.log').read_text(),row['mode']=='corrected')
        result=independent_score(metrics)
        assert metrics==row['metrics']
        assert abs(result['normalized_fom']-row['normalized_fom'])<1e-12
        assert result['feasible']==row['feasible']
        report={'existing_attempt':number,'new_simulations':0,'raw_to_units':metrics,
                'independent_strict_score':result,'mode':row['mode']}
        if row['mode']=='corrected':
            t,vin,vout,power=np.loadtxt(folder/'tran.tsv',skiprows=1).T
            static=abs(integral_mean(t,power,10e-12,90e-12))
            dynamic=abs(integral_mean(t,power,0,4e-9)-static)*1e6
            assert abs(dynamic-metrics['dynamic_power'])<.001
            assert abs(static-row['extras']['static_power_abs'])<1e-14
            report.update(static_power_W_from_vectors=static,dynamic_power_uW_from_vectors=dynamic,
                          static_component_independent_of_attempt_json=True,
                          dynamic_absolute_difference_uW=abs(dynamic-metrics['dynamic_power']))
        output.append(report)
    return {'scope':'Four representative archived exports; targeted audit only, no new measurements.',
            'new_simulations':0,'api_calls':0,'passed':True,'checks':output}

if __name__=='__main__':print(json.dumps(review(),indent=2))
