"""Exact local handoff contract; live model use is deliberately fail-closed."""
import ast
import hashlib
import json
from engine import EXP,CONFIG,load_task,parse_specs,save

class LiveLLMUnavailable(RuntimeError):
    pass

def source_prompt(name):
    tree = ast.parse((EXP/'upstream_reference/problem_agent_test.py').read_text())
    return next(ast.literal_eval(n.value) for n in tree.body
                if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)
                and n.targets[0].id==name)

def request(circuit,stage,history=None,feedback=None,understanding=None,remaining=None):
    cfg = load_task(circuit)
    context = {'circuit':circuit,'source_netlist_template':cfg['ota_subckt_template'],
               'source_testbench_template':cfg['testbench_template'],
               'fixed_parameters':cfg['params'],'variables':list(cfg['variable']),
               'released_values':{v:cfg['W_values'] for v in cfg['variable']},
               'width_scales':cfg['width_scales'],'source_specifications':cfg['user_specs_metric'],
               'metric_units':{k:v.get('unit') for k,v in cfg['metric_post'].items()},
               'measurement_port':'inverter time-weighted power and paired edges; otherwise source measurements',
               'actual_history_origin':'numerical baseline, not an LLM trajectory',
               'history':history or [],'feedback':feedback,'understanding':understanding,
               'remaining_attempts':remaining,'supported_inner_methods':['random','bayesian'],
               'normalization':'product(maximize metric / target) divided by product(minimize metric / target), excluding fom itself'}
    if stage=='circuit_understanding':
        context['actual_history_origin']=None
        metrics=[m for m in cfg['metrics'] if m!='fom']
        prompt=source_prompt('CIRCUIT_UNDERSTANDING_PROMPT').format(
            subckt_name=cfg['subckt_name'],ota_subckt_template=cfg['ota_subckt_template'],
            params=json.dumps(cfg['params']),variables=json.dumps({'names':list(cfg['variable']),'width_scales':cfg['width_scales']}),
            testbench_template=cfg['testbench_template'],metrics_list='\n'.join(metrics),
            impact_section_text='\n'.join(f'Explain qualitative impact on {m}.' for m in metrics),
            impact_json_str=json.dumps({m:'Describe circuit-grounded qualitative impact.' for m in metrics}))
    elif stage in ['initial_search_space','outer_regeneration']:
        # No hand-authored replacement of the missing CU result.
        prompt=('Return the author-style optimization_configuration JSON: variables_to_optimize maps variable '
                'names to objects with search_space arrays; variables_fixed maps remaining variables to '
                'objects with fixed_value. Cover every variable exactly once and use only released values. '
                'Include search_space_summary and reasoning. Use the actual supplied circuit understanding, '
                'history and feedback, and do not fabricate missing observations. '
                'If understanding is null, prerequisite CU has not run: do not treat this request as executed.')
    elif stage=='inner_iteration':
        prompt=('Return JSON {action: search|stop, method: random|bayesian, n_samples: integer, '
                'parameters: object, reasoning: string}. For search use only supported engines and '
                '1 <= n_samples <= remaining_attempts. Bayesian here means the documented GP-UCB port. '
                'Decide using actual simulation history and constraint feedback. No proposed size is an '
                'evaluated design until a simulator attempt has completed. Do not invent metrics.')
    else: raise ValueError(stage)
    return {'schema_version':'autosizer-local-controller-v1','stage':stage,'prompt':prompt,'context':context,
            'upstream_autosizer_commit':CONFIG['upstream_autosizer_commit'],
            'model_configuration_requested':{'model':'gemini-2.5-flash','temperature':.4,'top_p':.85,'top_k':20,'max_output_tokens':8192},
            'live_execution_authorized':False,'response_status':'not_requested_from_any_model',
            'source_prompt_reference':'upstream_reference/problem_agent_test.py and prompts.py; initial/inner/outer transport prompt is a local contract adaptation'}

def validate_response(circuit,stage,payload,remaining):
    cfg=load_task(circuit)
    if not isinstance(payload,dict): raise ValueError('JSON object required')
    if stage=='circuit_understanding':
        fields=['circuit_topology_overview','optimization_variables_mapping','optimization_variables_impact',
                'variable_interactions','key_insights_for_optimization']
        if not all(k in payload for k in fields):raise ValueError('Incomplete circuit understanding')
        return payload
    if stage=='inner_iteration':
        if payload.get('action')=='stop':return payload
        if payload.get('action')!='search' or payload.get('method') not in ['random','bayesian']:
            raise ValueError('Unsupported action/engine; never silently substitute')
        count=payload.get('n_samples')
        if type(count) is not int or not 1<=count<=remaining:raise ValueError('Attempt budget exceeded or invalid batch')
        if not isinstance(payload.get('parameters',{}),dict) or not isinstance(payload.get('reasoning'),str):
            raise ValueError('Invalid decision fields')
        return payload
    config=payload.get('optimization_configuration',{})
    active=config.get('variables_to_optimize',{})
    fixed=config.get('variables_fixed',{})
    if not isinstance(active,dict) or not isinstance(fixed,dict):raise ValueError('Variable maps required')
    if set(active)&set(fixed) or set(active)|set(fixed)!=set(cfg['variable']):
        raise ValueError('Every variable must be covered exactly once')
    choices={}
    for name,info in active.items():
        values=info.get('search_space') if isinstance(info,dict) else None
        if not isinstance(values,list) or not values or len(set(values))!=len(values) or any(v not in cfg['W_values'] for v in values):
            raise ValueError('Search values outside released domain')
        choices[name]=values
    fixed_values={}
    for name,info in fixed.items():
        value=info.get('fixed_value') if isinstance(info,dict) else info
        if value not in cfg['W_values']:raise ValueError('Fixed value outside released domain')
        fixed_values[name]=value
    combinations=1
    for values in choices.values():combinations*=len(values)
    return {'variables_to_optimize':choices,'variables_fixed':fixed_values,'num_combinations':combinations,
            'search_space_summary':payload.get('search_space_summary',{})}

def invoke_live(*_args,**_kwargs):
    raise LiveLLMUnavailable('External LLM calls prohibited in this tranche; no approved local model asset. No heuristic fallback.')

if __name__=='__main__':
    for circuit in CONFIG['circuits']:
        save(EXP/f'controller_requests/{circuit}_circuit_understanding.json',request(circuit,'circuit_understanding'))
    print('Prepared real circuit-understanding inputs; no live request sent.')
