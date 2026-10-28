"""Explicit numerical baselines. Nothing in this module is an LLM controller."""
import itertools
import json
import time
import warnings
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel,Matern,WhiteKernel
from threadpoolctl import threadpool_limits
from engine import EXP,CONFIG,evaluate,incumbent,load_task,save

def points(bounds):
    return list(itertools.product(*(range(lo,hi+1) for lo,hi in bounds)))

def feedback(history,bounds,previous_best):
    best = incumbent(history)
    valid = [r for r in history if r['measurement_valid']]
    feasible = [r for r in valid if r['feasible']]
    ordered = sorted(valid,key=lambda r:(r['feasible'],r['normalized_fom'] if r['feasible'] else -r['constraint_violation'],r['normalized_fom']),reverse=True)
    top = ordered[:5]
    best_value = best['normalized_fom'] if best and best['feasible'] else None
    improvement = None if previous_best is None or best_value is None else (best_value-previous_best)/max(abs(previous_best),1e-12)
    boundary = []
    for j,(lo,hi) in enumerate(bounds):
        observed = [r['indices'][j] for r in top]
        boundary.append({'variable_index':j,'bounds':[lo,hi],'top_indices':observed,
                         'lower_fraction':sum(x==lo for x in observed)/len(observed) if observed else None,
                         'upper_fraction':sum(x==hi for x in observed)/len(observed) if observed else None})
    return {'attempts':len(history),'valid':len(valid),'invalid':len(history)-len(valid),
            'feasible':len(feasible),'best_feasible_fom':best_value,'relative_improvement':improvement,
            'incumbent_indices':best['indices'] if best else None,'boundary_analysis':boundary}

def adapt(history,bounds,previous_best):
    report = feedback(history,bounds,previous_best)
    if report['incumbent_indices'] is None:
        return [[0,8] for _ in bounds],report|{'reason':'no valid data; restore released grid'}
    radius = 4 if report['feasible']==0 or (report['relative_improvement'] is not None and report['relative_improvement']<.001) else 2
    new = []
    for j,(lo,hi) in enumerate(bounds):
        center = report['incumbent_indices'][j]
        left,right = max(0,center-radius),min(8,center+radius)
        if center<=lo: left = min(left,max(0,lo-1))
        if center>=hi: right = max(right,min(8,hi+1))
        new.append([left,right])
    return new,report|{'radius':radius,'reason':'numerical incumbent/stagnation/boundary policy; not LLM'}

def propose_gp(candidates,history,rng):
    valid = [r for r in history if r['measurement_valid']]
    if len(valid)<3:
        return candidates[int(rng.integers(len(candidates)))],{'engine':'random_insufficient_valid_GP_data'}
    x = np.array([r['indices'] for r in valid],dtype=float)/8
    y = np.array([r['normalized_fom'] for r in valid])
    kernel = ConstantKernel(1.,constant_value_bounds='fixed')*Matern(length_scale=.35,length_scale_bounds='fixed',nu=2.5)+WhiteKernel(1e-6,noise_level_bounds='fixed')
    gp = GaussianProcessRegressor(kernel=kernel,optimizer=None,normalize_y=True,alpha=1e-10)
    with warnings.catch_warnings(record=True) as caught:
        gp.fit(x,y)
        mean,std = gp.predict(np.asarray(candidates,dtype=float)/8,return_std=True)
    ucb = mean+2*std
    largest = np.max(ucb)
    ties = np.flatnonzero(np.isclose(ucb,largest,rtol=0,atol=1e-12))
    pick = int(rng.choice(ties))
    return candidates[pick],{'engine':'GP_UCB','training_valid_observations':len(valid),
                            'predicted_mean':float(mean[pick]),'predicted_std':float(std[pick]),
                            'acquisition':float(ucb[pick]),'warnings':[str(w.message) for w in caught]}

def run(circuit,method,seed,budget,initial,checkpoints,stage):
    name = f'{circuit}__{method}__seed{seed}'
    out = EXP/'results'/stage/name
    if (out/'summary.json').exists():
        raise RuntimeError(f'Refusing to overwrite existing run {out}')
    out.mkdir(parents=True)
    n = len(load_task(circuit)['variable'])
    central = [[1,7] for _ in range(n)]
    all_points = points([[0,8] for _ in range(n)])
    initial_grid = points(central)
    init_rng = np.random.default_rng(seed)
    initialization = [initial_grid[i] for i in init_rng.choice(len(initial_grid),size=initial,replace=False)]
    rng = np.random.default_rng(seed+100003)
    history,decisions,outer = [],[],[]
    bounds = [b[:] for b in central]
    previous_best = None
    start = time.monotonic()
    with threadpool_limits(limits=1):
        for t in range(budget):
            if t == initial and method in ['random_full','gp_full']:
                bounds = [[0,8] for _ in range(n)]
            if t in checkpoints:
                if method == 'adaptive_gp':
                    new,report = adapt(history,bounds,previous_best)
                    outer.append({'after_attempt':t,'before_bounds':bounds,'after_bounds':new,'feedback':report})
                    bounds = new
                else:
                    report = feedback(history,bounds,previous_best)
                    outer.append({'after_attempt':t,'before_bounds':bounds,'after_bounds':bounds,
                                  'feedback':report,'action':'no range change in control'})
                previous_best = report['best_feasible_fom']
            seen = {tuple(r['indices']) for r in history}
            decision_start = time.monotonic()
            if t < initial:
                chosen,detail = initialization[t],{'engine':'common_central_random_initialization'}
            else:
                domain = all_points if method in ['random_full','gp_full'] else points(bounds)
                candidates = [x for x in domain if x not in seen]
                if not candidates:
                    if method == 'gp_frozen': raise RuntimeError('Frozen-domain exhausted before fixed budget')
                    old = bounds
                    bounds = [[0,8] for _ in range(n)]
                    candidates = [x for x in all_points if x not in seen]
                    outer.append({'after_attempt':t,'before_bounds':old,'after_bounds':bounds,
                                  'feedback':{'reason':'current domain exhausted; expand full released grid'}})
                if method == 'random_full':
                    chosen,detail = candidates[int(rng.integers(len(candidates)))],{'engine':'uniform_random_unseen'}
                else:
                    chosen,detail = propose_gp(candidates,history,rng)
            decisions.append({'attempt_within_run':t+1,'indices':list(chosen),'bounds':bounds,
                              'detail':detail,'decision_wall_seconds':time.monotonic()-decision_start})
            row = evaluate(circuit,list(chosen),{'stage':stage,'run':name,'within_run':t+1,
                                                'method':method,'seed':seed})
            history.append(row)
            save(out/'history.json',history)
            save(out/'decisions.json',decisions)
            save(out/'outer_feedback.json',outer)
    best = incumbent(history)
    feasible = [r for r in history if r['status']=='valid_feasible']
    summary = {'run':name,'circuit':circuit,'method':method,'seed':seed,'stage':stage,
               'budget':budget,'attempts':len(history),'unique_points':len({tuple(r['indices']) for r in history}),
               'valid':sum(r['measurement_valid'] for r in history),'invalid':sum(not r['measurement_valid'] for r in history),
               'feasible_candidates':len(feasible),'first_feasible_attempt':next((i+1 for i,r in enumerate(history) if r['feasible']),None),
               'best_feasible_fom':max((r['normalized_fom'] for r in feasible),default=None),
               'selected_indices':best['indices'] if best else None,'selected_global_attempt':best['global_attempt'] if best else None,
               'selected_is_feasible':best['feasible'] if best else False,
               'wall_seconds':time.monotonic()-start,
               'simulator_wall_seconds':sum(r['wall_seconds'] for r in history),
               'simulator_cpu_seconds':sum(r['child_cpu_seconds'] for r in history),
               'decision_wall_seconds':sum(d['decision_wall_seconds'] for d in decisions),
               'outer_range_changes':sum(r['before_bounds']!=r['after_bounds'] for r in outer),
               'initialization':initialization,'early_stop_on_feasibility':False,'model_calls':0}
    save(out/'summary.json',summary)
    print(json.dumps({k:summary[k] for k in ['run','attempts','first_feasible_attempt','best_feasible_fom','invalid','outer_range_changes']}),flush=True)
    return summary

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('stage',choices=['pilot','main'])
    args = parser.parse_args()
    config = CONFIG['pilot'] if args.stage=='pilot' else CONFIG
    if args.stage=='main':
        checks = json.loads((EXP/'results/pilot_checks.json').read_text())
        assert checks['passed'], 'Pilot must pass before scaling'
    summaries = []
    for circuit in config['circuits']:
        for seed in config['seeds']:
            for method in config['methods']:
                summaries.append(run(circuit,method,seed,
                    config['budget'] if args.stage=='pilot' else config['budget_per_main_run'],
                    config['initial_points'] if args.stage=='pilot' else config['common_initial_points'],
                    config['outer_update_at'],args.stage))
    save(EXP/f'results/{args.stage}_summaries.json',summaries)
