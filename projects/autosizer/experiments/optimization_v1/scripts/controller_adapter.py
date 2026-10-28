"""Prepared controller-to-numerical-engine bridge. Disabled in this tranche."""
import itertools
import numpy as np
from engine import CONFIG,evaluate,load_task
from llm_interface import LiveLLMUnavailable,validate_response
from search import propose_gp

def domain_from_response(circuit,response):
    """Pure conversion of the author's active/fixed schema to released-grid indices."""
    normalized=validate_response(circuit,'initial_search_space',response,remaining=0)
    cfg=load_task(circuit)
    ordered=[]
    for name in cfg['variable']:
        values=normalized['variables_to_optimize'].get(name)
        if values is None:values=[normalized['variables_fixed'][name]]
        ordered.append([cfg['W_values'].index(v) for v in values])
    return list(itertools.product(*ordered)),normalized

def proposal_from_decision(circuit,space_response,decision,history,remaining,seed):
    """Pure proposal preparation; no simulator/model call or measurement fabrication."""
    validated=validate_response(circuit,'inner_iteration',decision,remaining)
    if validated['action']=='stop':return None,{'action':'stop'}
    domain,_=domain_from_response(circuit,space_response)
    seen={tuple(row['indices']) for row in history}
    candidates=[point for point in domain if point not in seen]
    if not candidates:raise ValueError('Controller domain exhausted; request outer regeneration rather than fabricate designs')
    rng=np.random.default_rng(seed)
    if validated['method']=='random':
        return candidates[int(rng.integers(len(candidates)))],{'engine':'controller_selected_random'}
    # Reported supported method is a port, not the exact source skopt engine.
    return propose_gp(candidates,history,rng)

def execute_approved_decision(circuit,space_response,decision,history,remaining,seed,context):
    """Connection is concrete, but cannot execute synthetic/replayed decisions here."""
    if not CONFIG['external_model_calls_allowed']:
        raise LiveLLMUnavailable('Controller-driven execution is disabled by the frozen tranche; numerical experiments use named non-LLM policies.')
    validate_response(circuit,'inner_iteration',decision,remaining)
    if decision['action']=='stop':return []
    domain,_=domain_from_response(circuit,space_response)
    unseen=set(domain)-{tuple(row['indices']) for row in history}
    if len(unseen)<decision['n_samples']:
        raise ValueError('Requested batch exceeds unseen legal points; regenerate space before simulation')
    rows=[]
    for offset in range(decision['n_samples']):
        point,detail=proposal_from_decision(circuit,space_response,decision,history+rows,remaining,seed+offset)
        row=evaluate(circuit,list(point),context|{'controller_selected_method':decision['method'],
                                                'proposal_detail':detail,'batch_offset':offset})
        rows.append(row)
    return rows

if __name__=='__main__':
    # Domain/proposal-only software fixtures. Never represented as model outputs.
    space={'optimization_configuration':{'variables_to_optimize':{'W_pmos_base':{'search_space':[.84,1.05]}},
                                        'variables_fixed':{'W_nmos_base':{'fixed_value':1.68}}}}
    domain,_=domain_from_response('inverter',space)
    assert domain==[(0,4),(1,4)]
    decision={'action':'search','method':'random','n_samples':1,'parameters':{},'reasoning':'synthetic bridge check'}
    candidate,_=proposal_from_decision('inverter',space,decision,[],1,11)
    assert candidate in domain
    try:execute_approved_decision('inverter',space,decision,[],1,11,{'stage':'synthetic_must_not_execute'})
    except LiveLLMUnavailable:pass
    else:raise AssertionError('Controller gate did not block simulation')
    print('Active/fixed-domain bridge and fail-closed dispatch verified with synthetic proposal-only fixtures; zero simulator/model calls.')
