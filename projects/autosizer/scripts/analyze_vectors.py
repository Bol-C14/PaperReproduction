"""Independent read-only electrical measurement checks on preserved simulator exports."""
from pathlib import Path
import json
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
attempts = json.loads((ROOT / 'logs/attempts.json').read_text())
analysis = []
def crossing(t, y, direction):
    pair = (y[:-1] < .9) & (y[1:] >= .9) if direction == 'rise' else (y[:-1] > .9) & (y[1:] <= .9)
    indices = np.flatnonzero(pair)
    return [float(t[i] + (.9-y[i])*(t[i+1]-t[i])/(y[i+1]-y[i])) for i in indices]

for attempt in attempts:
    if attempt['variant'] != 'repaired_export':
        continue
    folder = Path(attempt['cwd'])
    row = {'attempt': attempt['attempt'], 'circuit': attempt['circuit'],
           'diagnostic_refinement': attempt['diagnostic_refinement']}
    if attempt['circuit'] == 'inverter':
        data = np.loadtxt(folder/'tran.tsv', skiprows=1)
        t, vin, vout, power = data.T
        input_rise, input_fall = crossing(t, vin, 'rise'), crossing(t, vin, 'fall')
        output_rise, output_fall = crossing(t, vout, 'rise'), crossing(t, vout, 'fall')
        tphl = (next(x for x in output_fall if x >= input_rise[0])-input_rise[0])*1e12
        tplh = (next(x for x in output_rise if x >= input_fall[0])-input_fall[0])*1e12
        mean_power = float(np.trapezoid(power, t)/(t[-1]-t[0]))
        static_power = attempt['extra_raw_metrics']['static_power_abs']
        dynamic_uw = abs(mean_power-static_power)*1e6
        dc = np.loadtxt(folder/'dc.tsv', skiprows=1)
        derivative_gain_db = float(20*np.log10(np.max(np.abs(np.gradient(dc[:,2], dc[:,1])))))
        gain = attempt['metrics']['dc_gain_db']
        delay = (tphl+tplh)/2
        fom = (gain/20)/((delay/50)*(dynamic_uw/50))
        row.update(independent_tphl_ps=tphl, independent_tplh_ps=tplh,
                   independent_average_delay_ps=delay, integrated_dynamic_power_uw=dynamic_uw,
                   ngspice_integrated_dynamic_power_uw=attempt['extra_raw_metrics']['dynamic_power_timeweighted']*1e6,
                   sample_mean_dynamic_power_uw=attempt['metrics']['dynamic_power'],
                   dc_central_difference_gain_db=derivative_gain_db,
                   source_deriv_gain_db=gain,
                   normalized_fom_using_integrated_power=fom,
                   constraints_integrated={'fom>1': fom>1, 'gain>20': gain>20,
                                           'delay<50': delay<50, 'power<50': dynamic_uw<50})
        row['status_using_integrated_power'] = 'valid_feasible' if all(row['constraints_integrated'].values()) else 'valid_infeasible'
    else:
        data = np.loadtxt(folder/'ac.tsv', skiprows=1)
        f, mag = data[:,0], data[:,1]
        db = 20*np.log10(mag)
        indices = np.flatnonzero((db[:-1]>0)&(db[1:]<=0))
        if not len(indices):
            row.update(status='no_downward_unity_gain_crossing', independent_ugbw_mhz=None)
        else:
            i = int(indices[0])
            unity = float((f[i]-db[i]*(f[i+1]-f[i])/(db[i+1]-db[i]))*1e-6)
            row.update(independent_gain_db=float(db[0]), independent_ugbw_mhz=unity,
                       source_gain_db=attempt['metrics']['dc_gain_db'],
                       source_ugbw_mhz=attempt['metrics']['ugbw'],
                       source_supply_power_uw=attempt['metrics']['power_dc'])
    analysis.append(row)
(ROOT/'results/vector_crosschecks.json').write_text(json.dumps(analysis, indent=2))
print(json.dumps(analysis, indent=2))
