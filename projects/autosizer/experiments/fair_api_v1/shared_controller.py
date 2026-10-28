"""Project adapter to the shared public chat interface; no HTTP/key loading code.

Current shared chat lacks request_options. Live integration fails closed until its
owner exposes/honors public request controls. No private _request/_transport bypass.
"""
import copy
from decimal import Decimal
import inspect
import json
import sys
import itertools
from pathlib import Path
from fair_runtime import (AttemptLedger,BudgetError,CONFIG,CAPS,STAGES,
                          check_input,atomic)

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'april_api_stage'))
from api_controller import validate,parse_json

class SharedInterfaceIncomplete(RuntimeError):pass
class AuthorizationPending(RuntimeError):pass

class SharedController:
    def __init__(self,client,ledger,*,run_id,token_counter,evidence_dir):
        self.client,self.ledger,self.run_id=client,ledger,run_id
        self.token_counter,self.evidence_dir=token_counter,Path(evidence_dir)
    def check_interface(self):
        # Explicit parameter, not **kwargs silently swallowing controls.
        if 'request_options' not in inspect.signature(self.client.chat).parameters:
            raise SharedInterfaceIncomplete('Shared Client.chat must expose and honor request_options; current provider overwrite cannot enforce standard price/reasoning policy')
        settings=self.client.config.public_settings()
        if settings.get('chat_model')!='google/gemini-2.5-flash':
            raise SharedInterfaceIncomplete('Shared fixed model differs from frozen project model')
        return True
    def call(self,stage,messages,*,authorize_live=False):
        if not authorize_live or CONFIG.get('execution_enabled') is not True:
            raise AuthorizationPending('Project execution policy, parent authorization and shared live gate must all permit execution')
        self.check_interface()
        check=check_input(messages,token_counter=self.token_counter)
        attempt=self.ledger.reserve_api(stage,check)
        folder=self.evidence_dir/attempt
        folder.mkdir(parents=True,exist_ok=False)
        options=copy.deepcopy(CONFIG['request_template'])
        options.pop('model');options.pop('stream')
        maximum=CAPS['output_per_stage'][stage]
        record=next(r for r in self.ledger.data['api'] if r['attempt_id']==attempt)
        atomic(folder/'request.json',{'stage':stage,'messages':messages,'max_tokens':maximum,
                                      'request_options':options,'input_check':check})
        try:
            # Shared client owns global slots, private credential loading and locked
            # global USD reservation/finish ledger. Local cap never replaces these.
            response=self.client.chat(messages,project='autosizer',run_id=self.run_id,
                         max_tokens=maximum,max_cost_usd=record['maximum_token_cost_usd'],
                         authorize_live=authorize_live,request_options=options)
        except Exception as error:
            self.ledger.finish_api(attempt,'transport_failure')
            atomic(folder/'error.json',{'type':type(error).__name__,'status':'shared_request_failed','project_reservation_not_refunded':True})
            raise BudgetError('Shared request failed; attempt remains charged; no automatic retry') from None
        # Archive only useful response content/metadata, never private config/headers.
        public={k:response.get(k) for k in ('id','model','provider','service_tier','usage','choices')}
        atomic(folder/'response.json',public)
        try:
            usage=response['usage']
            if response.get('model')!='google/gemini-2.5-flash':raise ValueError('Model mismatch')
            if response.get('provider') not in ('Google AI Studio','google-ai-studio'):raise ValueError('Provider mismatch')
            if response.get('service_tier','default')!='default':raise ValueError('Nonstandard tier')
            for key,limit in [('prompt_tokens',check['input_tokens_upper_bound']),('completion_tokens',maximum)]:
                value=usage.get(key)
                if type(value) is not int or not 0<=value<=limit:raise ValueError('Usage/token bound mismatch')
            reasoning=usage.get('completion_tokens_details',{}).get('reasoning_tokens')
            if reasoning is not None and (type(reasoning) is not int or reasoning!=0):raise ValueError('Nonzero or invalid reasoning usage')
            if usage.get('cost') is not None:
                cost=Decimal(str(usage['cost']))
                if not cost.is_finite() or not 0<=cost<=Decimal(record['maximum_token_cost_usd']):raise ValueError('Usage cost exceeds reservation')
            # If actual cost is unknown, shared and project accounting retain
            # the full reserved bound; no refund or invented zero cost.
        except (KeyError,ValueError,TypeError,ArithmeticError):
            self.ledger.finish_api(attempt,'provider_or_usage_mismatch')
            atomic(folder/'error.json',{'status':'provider_or_usage_mismatch','further_calls_blocked':True})
            raise BudgetError('Provider/usage policy failed; stop and reconcile') from None
        try:
            content=response['choices'][0]['message']['content']
            if response['choices'][0].get('finish_reason')!='stop':raise ValueError('Truncated/nonstop response')
            if not isinstance(content,str):raise ValueError('Text content required')
            value=parse_json(content)
            if not isinstance(value,dict):raise ValueError('JSON object required')
            source_stage='inner_iteration' if stage in ('inner_first','inner_second') else stage
            validate(source_stage,value,remaining=self.ledger.remaining('api_guided'))
            if source_stage=='inner_iteration' and value['action']=='search' and value['n_samples']!=12:
                raise ValueError('Exact twelve-attempt batch required')
            if source_stage in ('initial_search_space','outer_regeneration'):
                context=json.loads(messages[1]['content'])['context']
                cfg=value['optimization_configuration']
                active,fixed=cfg['variables_to_optimize'],cfg['variables_fixed']
                choices=[]
                grid=context['W_values']
                for name in ('W_pmos_base','W_nmos_base'):
                    if name in active:choices.append([grid.index(v) for v in active[name]['search_space']])
                    else:
                        v=fixed[name]
                        choices.append([grid.index(v['fixed_value'] if isinstance(v,dict) else v)])
                seen={tuple(r['indices']) for r in context['history']}
                if len(set(itertools.product(*choices))-seen)<12:raise ValueError('Insufficient unseen domain')
        except (KeyError,IndexError,ValueError,TypeError) as error:
            self.ledger.finish_api(attempt,'schema_invalid')
            atomic(folder/'error.json',{'status':'schema_invalid','validation_error':str(error),'retry_requires_full_raw_response_and_new_charged_attempt':True})
            raise BudgetError('Invalid/truncated JSON; exact response preserved; stage retry remains charged') from None
        self.ledger.finish_api(attempt,'valid')
        return value
