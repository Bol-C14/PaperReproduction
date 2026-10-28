"""Descriptive matched-budget comparisons; no significance or LLM attribution."""
from pathlib import Path
import csv
import datetime as dt
import hashlib
import importlib.metadata as metadata
import json
import statistics as stats
from engine import EXP,CONFIG,save
from llm_interface import request,validate_response,invoke_live,LiveLLMUnavailable

summaries=json.loads((EXP/'results/main_summaries.json').read_text())
per_run=[]
for summary in summaries:
    history=json.loads((EXP/'results/main'/summary['run']/'history.json').read_text())
    best=summary['best_feasible_fom']
    selected=next(r for r in history if r['global_attempt']==summary['selected_global_attempt'])
    per_run.append({'run':summary['run'],'circuit':summary['circuit'],'method':summary['method'],
                    'seed':summary['seed'],'evaluations_to_best_feasible':next((i+1 for i,r in enumerate(history)
                      if r['feasible'] and r['normalized_fom']==best),None),'selected_metrics':selected['metrics']})
save(EXP/'results/analysis_per_run.json',per_run)
oracle=json.loads((EXP/'results/oracle_summary.json').read_text())
validation=json.loads((EXP/'results/validation.json').read_text())
rows=[]
for circuit in CONFIG['circuits']:
    for method in CONFIG['methods']:
        selected=[s for s in summaries if s['circuit']==circuit and s['method']==method]
        foms=[s['best_feasible_fom'] for s in selected if s['best_feasible_fom'] is not None]
        row={'circuit':circuit,'method':method,'seeds':[s['seed'] for s in selected],
             'best_feasible_fom_per_seed':[s['best_feasible_fom'] for s in selected],
             'mean_best_feasible_fom':stats.mean(foms) if foms else None,
             'sd_best_feasible_fom':stats.stdev(foms) if len(foms)>1 else 0.,
             'first_feasible_per_seed':[s['first_feasible_attempt'] for s in selected],
             'mean_first_feasible':stats.mean(s['first_feasible_attempt'] for s in selected if s['first_feasible_attempt'] is not None),
             'runs_with_feasible_design':len(foms),'attempts_per_run':36,
             'feasible_candidates_per_seed':[s['feasible_candidates'] for s in selected],
             'invalid':sum(s['invalid'] for s in selected),
             'mean_simulator_cpu_seconds':stats.mean(s['simulator_cpu_seconds'] for s in selected),
             'mean_run_wall_seconds':stats.mean(s['wall_seconds'] for s in selected),
             'range_changes_per_seed':[s['outer_range_changes'] for s in selected]}
        if circuit=='inverter':
            best=oracle['best_feasible_fom']
            row['relative_regret_per_seed']=[(best-s['best_feasible_fom'])/best for s in selected]
            row['grid_optimum_hits']=sum(abs(best-s['best_feasible_fom'])<1e-10 for s in selected)
        rows.append(row)
save(EXP/'results/comparison.json',{'rows':rows,'oracle':oracle,'statistical_scope':'3 seeds, descriptive only',
     'paper_LLM_results':False,'main_candidate_attempts':864,'main_real_process_calls':864})
with (EXP/'results/comparison.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['circuit','method','mean_best_feasible_fom','sd','first_feasible_seed11','first_feasible_seed29','first_feasible_seed47','grid_optimum_hits'])
    for r in rows:w.writerow([r['circuit'],r['method'],r['mean_best_feasible_fom'],r['sd_best_feasible_fom'],*r['first_feasible_per_seed'],r.get('grid_optimum_hits')])

paired=[]
for circuit in CONFIG['circuits']:
    for seed in CONFIG['seeds']:
        s={r['method']:r for r in summaries if r['circuit']==circuit and r['seed']==seed}
        paired.append({'circuit':circuit,'seed':seed,
                       'adaptive_minus_full_gp':s['adaptive_gp']['best_feasible_fom']-s['gp_full']['best_feasible_fom'],
                       'adaptive_minus_frozen_gp':s['adaptive_gp']['best_feasible_fom']-s['gp_frozen']['best_feasible_fom'],
                       'full_gp_minus_random':s['gp_full']['best_feasible_fom']-s['random_full']['best_feasible_fom']})
save(EXP/'results/paired_differences.json',paired)

# Actual source/feedback requests, without any model-generated or replayed answer.
for circuit in CONFIG['circuits']:
    run=f'{circuit}__adaptive_gp__seed11'
    folder=EXP/'results/main'/run
    history=json.loads((folder/'history.json').read_text())[:12]
    events=json.loads((folder/'outer_feedback.json').read_text())
    feedback=next(e['feedback'] for e in events if e['after_attempt']==12)
    compact=[{k:r[k] for k in ['indices','variables','metrics','normalized_fom','constraints','feasible','status','global_attempt']} for r in history]
    for stage in ['circuit_understanding','initial_search_space','inner_iteration','outer_regeneration']:
        payload=request(circuit,stage,compact if stage!='circuit_understanding' else None,
                        feedback if stage in ['inner_iteration','outer_regeneration'] else None,
                        understanding=None,remaining=24)
        save(EXP/f'controller_requests/{circuit}_{stage}.json',payload)

# Synthetic interface rejection checks are not controller responses or circuit labels.
accepted=validate_response('inverter','inner_iteration',{'action':'search','method':'bayesian','n_samples':4,'parameters':{},'reasoning':'synthetic contract test'},4)
bad=[{'action':'search','method':'bayesian','n_samples':5,'reasoning':'synthetic'},
     {'action':'search','method':'unimplemented','n_samples':1,'reasoning':'synthetic'},
     {'action':'search','method':'random','n_samples':True,'reasoning':'synthetic'}]
for b in bad:
    try:validate_response('inverter','inner_iteration',b,4)
    except ValueError:pass
    else:raise AssertionError('Invalid decision accepted')
good_space={'optimization_configuration':{'variables_to_optimize':{'W_pmos_base':{'search_space':[.84,1.05]}},'variables_fixed':{'W_nmos_base':{'fixed_value':1.68}}}}
assert validate_response('inverter','initial_search_space',good_space,4)['num_combinations']==2
bad_space={'optimization_configuration':{'variables_to_optimize':{'W_pmos_base':{'search_space':[999.]}},'variables_fixed':{'W_nmos_base':{'fixed_value':1.68}}}}
try:validate_response('inverter','outer_regeneration',bad_space,4)
except ValueError:pass
else:raise AssertionError('Out-of-domain space accepted')
try:invoke_live()
except LiveLLMUnavailable as error:blocked=str(error)
else:raise AssertionError('Live gate opened')
save(EXP/'results/interface_checks.json',{'synthetic_contract_checks_passed':7,'synthetic_not_model_responses':True,
     'actual_input_requests':8,'model_calls':0,'live_controller_status':'blocked_by_tranche_no_external_LLM_permission_and_no_local_model_asset',
     'gate_message':blocked,'source_circuit_understanding_prompt_rendered':True,
     'other_transport_prompts':'local source-grounded contract adaptations; supported pool restricted to random and GP-UCB'})

attempts=[json.loads(p.read_text()) for p in sorted((EXP/'logs/attempts').glob('*/attempt.json'))]
counts={}
for r in attempts:counts[r['context']['stage']]=counts.get(r['context']['stage'],0)+1
manifest=json.loads((EXP/'configs/execution_manifest.json').read_text())
save(EXP/'results/resource_ledger.json',{'started_utc':CONFIG['created_utc'],'finished_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
     'attempts':len(attempts),'attempts_by_stage':counts,'hard_cap':CONFIG['max_simulator_attempts'],
     'all_attempts_finished':all(r['status']!='launch_pending' for r in attempts),
     'invalid_attempts':sum(not r['measurement_valid'] for r in attempts),
     'simulator_wall_seconds_sum':sum(r['wall_seconds'] for r in attempts),
     'simulator_child_cpu_seconds_sum':sum(r['child_cpu_seconds'] for r in attempts),
     'simulator_max_rss_kib_upper_bound':max(r['child_peak_rss_kib_upper_bound'] for r in attempts),
     'main_run_wall_seconds_sum':sum(s['wall_seconds'] for s in summaries),
     'main_decision_wall_seconds_sum':sum(s['decision_wall_seconds'] for s in summaries),
     'gpu_used':False,'paid_resources':False,'external_model_calls':0,'additional_download_bytes':0,
     'protocol_commit':manifest['protocol_and_implementation_commit'],'versions':manifest['packages'],
     'limits':'20 s wall and 15 s CPU / simulator process, 2 GiB child address space, current quota, two-hour phase deadline',
     'model_weights_found_in_bounded_workspace_opt_inventory':False})

flips=[{'run':v['run'],'original_feasible':v['original']['feasible'],'refined_feasible':v['refined']['feasible']}
       for v in validation if v['original']['feasible']!=v['refined']['feasible']]
save(EXP/'results/validation_summary.json',{'winner_runs':len(validation),'remeasurement_calls':48,
     'all_original_valid':all(v['original']['measurement_valid'] for v in validation),
     'all_refined_valid':all(v['refined']['measurement_valid'] for v in validation),
     'all_refined_winners_feasible':all(v['refined']['feasible'] for v in validation),
     'original_vs_refined_feasibility_flips':flips,'winner_replacements':0})
print(json.dumps({'comparison':rows,'oracle':oracle,'validation_flips':flips},indent=2))
