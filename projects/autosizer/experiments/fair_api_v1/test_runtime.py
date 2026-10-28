"""Mock-only executable-sequence/budget tests. No simulator or network calls."""
from decimal import Decimal
import importlib.util
import inspect
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from fair_runtime import (AttemptLedger,FairBatchRunner,PLAN,DOMAIN,STAGES,CONFIG,
     BudgetError,InputLimitExceeded,TokenCounterRequired,build_messages,check_input,
     correction_messages,pending_payload)
from shared_controller import SharedController,SharedInterfaceIncomplete,AuthorizationPending

CU={name:'SYNTHETIC OFFLINE TEST ONLY' for name in ('circuit_topology_overview',
    'optimization_variables_mapping','optimization_variables_impact','variable_interactions','key_insights_for_optimization')}
VALUES=[.84,1.05,1.26,1.47,1.68,1.89,2.1,2.31,2.52]
DOMAIN_RESPONSE={'optimization_configuration':{'variables_to_optimize':{name:{'search_space':VALUES} for name in ('W_pmos_base','W_nmos_base')},'variables_fixed':{}},'reasoning':'SYNTHETIC ONLY'}

def certificate(messages):
    # Synthetic contract fixture, not a model tokenizer and not approved for live use.
    return {'model':'google/gemini-2.5-flash','framing_included':True,
            'certified_upper_bound':True,'tokens':4000,'counter_id':'OFFLINE_TEST_STUB_NOT_A_TOKENIZER'}

def observation(attempt,point,origin,status='valid_infeasible'):
    valid=status.startswith('valid_')
    return {'attempt_id':attempt,'origin':origin,'indices':list(point),
            'variables':dict(zip(('W_pmos_base','W_nmos_base'),(VALUES[point[0]],VALUES[point[1]]))),
            'status':status,'measurement_valid':valid,
            'metrics':{'dc_gain_db':24.,'average_delay':20.,'dynamic_power':65.} if valid else {'dc_gain_db':None,'average_delay':None,'dynamic_power':None},
            'normalized_fom':2.3 if valid else None,'constraints':{'fom':True,'dc_gain_db':True,'average_delay':True,'dynamic_power':False} if valid else {},
            'feasible':False,'constraint_violation':.3 if valid else None}

def initialized(ledger):
    rows=[]
    for point in PLAN['initial_indices']:
        attempt=ledger.reserve_spice(kind='common',indices=point)
        ledger.finish_spice(attempt,status='valid_infeasible',spawn_confirmed=True)
        rows.append(observation(attempt,point,'common'))
    ledger.freeze_common(rows)
    return rows

def fresh(ledger,count=12):
    rows=[]
    choices=[list(p) for p in DOMAIN if list(p) not in PLAN['initial_indices']]
    for i,point in enumerate(choices[:count]):
        attempt=ledger.reserve_spice(kind='search',arm='api_guided',indices=point)
        status=('valid_infeasible','measurement_invalid','solver_error','timeout')[i%4]
        ledger.finish_spice(attempt,status=status,spawn_confirmed=True)
        rows.append(observation(attempt,point,'api_guided',status))
    return rows

class MockExtendedShared:
    """Represents the required future public interface. No real client/credential."""
    def __init__(self,kind='valid'):
        self.config=SimpleNamespace(public_settings=lambda:{'chat_model':'google/gemini-2.5-flash'})
        self.calls=[];self.kind=kind
    def chat(self,messages,*,project,run_id,max_tokens,max_cost_usd,authorize_live=False,request_options=None):
        self.calls.append({'project':project,'run_id':run_id,'max_tokens':max_tokens,
                           'reservation':max_cost_usd,'authorize_live':authorize_live,'request_options':request_options})
        if self.kind=='failure':raise RuntimeError('MOCK_TRANSPORT_FAILURE')
        stage=json.loads(messages[1]['content'])['stage']
        value=CU if stage=='circuit_understanding' else DOMAIN_RESPONSE if stage in ('initial_search_space','outer_regeneration') else {'action':'search','method':'bayesian','n_samples':12,'parameters':{},'reasoning':'SYNTHETIC ONLY'}
        if self.kind=='extra_fixed' and stage in ('initial_search_space','outer_regeneration'):
            import copy
            value=copy.deepcopy(value);value['optimization_configuration']['variables_fixed']={'L':{'fixed_value':.15}}
        content='invalid JSON' if self.kind=='invalid' else json.dumps(value)
        return {'id':'MOCK_ONLY','model':'google/gemini-2.5-flash','provider':'Google AI Studio','service_tier':'default',
                'choices':[{'message':{'content':content},'finish_reason':'stop'}],
                'usage':{'prompt_tokens':1000,'completion_tokens':100,'completion_tokens_details':{'reasoning_tokens':1 if self.kind=='reasoning' else 0},'cost':.00055}}

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.ledger=AttemptLedger(self.root/'ledger.json')
        self.common=initialized(self.ledger)
        # Local project gate is enabled only in-memory inside mock tests. Shared
        # flags/configuration are never changed or loaded. Disk policy stays false.
        policy=patch('shared_controller.CONFIG',dict(CONFIG,execution_enabled=True))
        policy.start();self.addCleanup(policy.stop)
    def messages(self,stage,rows=()):
        return build_messages(stage,ledger=self.ledger,common_rows=self.common,
                              arm_rows=list(rows),understanding=None if stage=='circuit_understanding' else CU,
                              domain=PLAN['initial_domain'])
    def test_ten_common_twelve_fresh_remaining_twelve(self):
        rows=fresh(self.ledger)
        context=json.loads(self.messages('inner_second',rows)[1]['content'])['context']
        self.assertEqual((len(context['history']),context['fresh_attempts_used'],context['remaining_attempts']),(22,12,12))
        self.assertEqual(self.ledger.remaining('fixed_gp'),24)
    def test_changed_common_values_cannot_diverge_between_arms(self):
        import copy
        changed=copy.deepcopy(self.common);changed[0]['metrics']['dc_gain_db']=99.
        with self.assertRaises(ValueError):self.ledger.freeze_common(changed)
        with self.assertRaises(ValueError):FairBatchRunner(self.ledger,'fixed_gp',changed)
    def test_spice_invalid_failed_retry_and_pending_all_debit(self):
        point=next(p for p in DOMAIN if list(p) not in PLAN['initial_indices'])
        first=self.ledger.reserve_spice(kind='search',arm='api_guided',indices=point)
        self.ledger.finish_spice(first,status='measurement_invalid',spawn_confirmed=True)
        retry=self.ledger.reserve_spice(kind='search',arm='api_guided',indices=point,retry_of=first)
        self.ledger.finish_spice(retry,status='launch_error',spawn_confirmed=False)
        self.ledger.reserve_spice(kind='search',arm='api_guided',indices=point,retry_of=retry)
        self.assertEqual(self.ledger.remaining('api_guided'),21)
        self.assertEqual(AttemptLedger(self.root/'ledger.json').remaining('api_guided'),21)
    def test_batch_runner_charges_before_failed_evaluator(self):
        runner=FairBatchRunner(self.ledger,'api_guided',self.common)
        point=next(p for p in DOMAIN if list(p) not in PLAN['initial_indices'])
        def evaluate(point,attempt):
            self.assertEqual(self.ledger.remaining('api_guided'),23)
            raise TimeoutError('SYNTHETIC_UNCERTAIN_OUTCOME')
        with self.assertRaises(BudgetError):runner.run_batch(1,propose=lambda history:point,evaluate=evaluate)
        self.assertEqual(self.ledger.remaining('api_guided'),23)
        with self.assertRaises(BudgetError):FairBatchRunner(self.ledger,'api_guided',self.common)
    def test_missing_failed_history_not_silently_removed(self):
        rows=fresh(self.ledger)
        with self.assertRaises(ValueError):self.messages('outer_regeneration',rows[:-1])
    def test_token_and_byte_overflow_keep_context(self):
        messages=self.messages('circuit_understanding');before=json.dumps(messages)
        self.assertEqual(check_input(messages)['input_tokens_upper_bound'],1048576)
        self.assertEqual(check_input(messages)['admission_basis'],'official_context_envelope')
        with self.assertRaises(InputLimitExceeded):check_input(messages,token_counter=lambda _:dict(certificate(_),tokens=1048577))
        self.assertEqual(json.dumps(messages),before)
        retry=correction_messages(messages,'X'*65536,'schema mismatch')
        with self.assertRaises(InputLimitExceeded):check_input(retry,token_counter=certificate)
        self.assertEqual(retry[2]['content'],'X'*65536)
    def test_context_envelope_ten_attempt_cost_upper_bound(self):
        messages=self.messages('circuit_understanding')
        check=check_input(messages)
        for stage in STAGES:
            for _ in range(2):
                attempt=self.ledger.reserve_api(stage,check);self.ledger.finish_api(attempt,'valid')
        self.assertEqual(sum(r['input_tokens_reserved'] for r in self.ledger.data['api']),10485760)
        self.assertEqual(sum((Decimal(r['maximum_token_cost_usd']) for r in self.ledger.data['api']),Decimal(0)),Decimal('3.20'))
    def test_pending_payload_explicit_price_output_reasoning_and_tier(self):
        payload=pending_payload('inner_first',self.messages('inner_first'),token_counter=certificate)
        self.assertFalse(payload['execution_enabled']);body=payload['body']
        self.assertEqual(body['model'],'google/gemini-2.5-flash')
        self.assertEqual(body['service_tier'],'default')
        self.assertEqual(body['provider']['max_price'],{'prompt':.30,'completion':2.50,'request':0})
        self.assertEqual(body['provider']['only'],['google-ai-studio'])
        self.assertFalse(body['provider']['allow_fallbacks']);self.assertTrue(body['provider']['require_parameters'])
        self.assertEqual(body['reasoning'],{'enabled':False});self.assertEqual(body['max_tokens'],256)
    def controller(self,client):
        return SharedController(client,self.ledger,run_id='OFFLINE_TEST_ONLY',token_counter=certificate,evidence_dir=self.root/'evidence')
    def test_disabled_and_old_shared_interface_do_not_call(self):
        class Old:
            def chat(self,messages,*,project,run_id,max_tokens,max_cost_usd,authorize_live=False):self.fail('Must not call')
        with self.assertRaises(AuthorizationPending):self.controller(Old()).call('circuit_understanding',self.messages('circuit_understanding'))
        with self.assertRaises(SharedInterfaceIncomplete):self.controller(Old()).call('circuit_understanding',self.messages('circuit_understanding'),authorize_live=True)
        self.assertEqual(len(self.ledger.data['api']),0)
    def test_disk_pending_policy_blocks_even_explicit_authorize_flag(self):
        client=MockExtendedShared()
        with patch('shared_controller.CONFIG',dict(CONFIG,execution_enabled=False)):
            with self.assertRaises(AuthorizationPending):self.controller(client).call('circuit_understanding',self.messages('circuit_understanding'),authorize_live=True)
        self.assertEqual(client.calls,[])
    def test_mock_shared_call_preserves_shared_controls_and_reservation(self):
        client=MockExtendedShared()
        with patch('socket.socket',side_effect=AssertionError('Network forbidden')):
            result=self.controller(client).call('circuit_understanding',self.messages('circuit_understanding'),authorize_live=True)
        self.assertEqual(result,CU);call=client.calls[0]
        self.assertEqual(call['project'],'autosizer');self.assertEqual(call['request_options']['service_tier'],'default')
        self.assertEqual(Decimal(call['reservation']),Decimal('.32'))
    def test_api_failed_schema_retry_debit_api_not_spice(self):
        messages=self.messages('circuit_understanding')
        for kind in ('failure','invalid'):
            with self.assertRaises(BudgetError):self.controller(MockExtendedShared(kind)).call('circuit_understanding',messages,authorize_live=True)
        self.assertEqual(len(self.ledger.data['api']),2)
        self.assertEqual(self.ledger.remaining('api_guided'),24)
        with self.assertRaises(BudgetError):self.controller(MockExtendedShared()).call('circuit_understanding',messages,authorize_live=True)
    def test_usage_reasoning_mismatch_stops_further_calls(self):
        messages=self.messages('circuit_understanding')
        with self.assertRaises(BudgetError):self.controller(MockExtendedShared('reasoning')).call('circuit_understanding',messages,authorize_live=True)
        with self.assertRaises(BudgetError):self.controller(MockExtendedShared()).call('initial_search_space',self.messages('initial_search_space'),authorize_live=True)
        self.assertEqual(len(self.ledger.data['api']),1)
    def test_full_five_stage_sequence_and_ten_requests(self):
        client=MockExtendedShared();controller=self.controller(client)
        for stage in STAGES:
            rows=fresh(self.ledger) if stage=='outer_regeneration' else rows if stage=='inner_second' else []
            messages=self.messages(stage,rows)
            controller.call(stage,messages,authorize_live=True)
            # A second paid attempt is counted even if semantic validation will fail.
            check=check_input(correction_messages(messages,'SYNTHETIC INVALID OUTPUT','exact schema error'),token_counter=certificate)
            attempt=self.ledger.reserve_api(stage,check);self.ledger.finish_api(attempt,'schema_invalid')
        self.assertEqual(len(client.calls),5);self.assertEqual(len(self.ledger.data['api']),10)
        self.assertEqual(sum(r['output_tokens_reserved'] for r in self.ledger.data['api']),7168)
        self.assertEqual(self.ledger.remaining('api_guided'),12)
    def test_live_driver_complete_sequence_with_injected_shared_and_simulator(self):
        import sys
        import live_pilot
        import audit_live
        root=self.root/'MOCK_DRIVER_ONLY'
        client=MockExtendedShared()
        class FakeSimulator:
            def __init__(self):self.count=0
            def evaluate(self,point,origin,mode='corrected',export=False,refined=False):
                self.count+=1
                result=observation('MOCK',point,origin)
                result.update(attempt=self.count,returncode=0,mode=mode,export=export,refined=refined)
                folder=root/'attempts'/f'{self.count:03d}'
                folder.mkdir(parents=True)
                return result
        simulator=FakeSimulator()
        def freeze(args,module):root.mkdir();return simulator
        shared=SimpleNamespace(load_config=lambda:None,Client=lambda _:client)
        # The driver inspects the public method on Client before constructing it.
        class Factory:
            chat=MockExtendedShared.chat
            def __new__(cls,config):return client
        shared.Client=Factory
        args=SimpleNamespace(root=root,shared_module=Path('MOCK_SHARED/openrouter_shared.py'),binary=Path('MOCK_NGSPICE'),selector=Path('MOCK_SELECTOR'))
        with patch.dict(sys.modules,{'openrouter_shared':shared}),patch.object(live_pilot,'freeze',freeze),patch.object(audit_live,'audit_preflight',lambda root:(root/'preflight_checks.json').write_text('{"passed":true,"mock_only":true}')),patch.object(audit_live,'audit',lambda root:None),patch('socket.socket',side_effect=AssertionError('Network forbidden')):
            live_pilot.run(args)
        result=json.loads((root/'execution_summary.json').read_text())
        self.assertEqual((simulator.count,len(client.calls)),(63,5))
        self.assertTrue(result['matched_budget'])
        self.assertEqual((result['guided_fresh'],result['control_fresh']),(24,24))
        final_request=json.loads((root/'api/api_05/request.json').read_text())
        context=json.loads(final_request['messages'][1]['content'])['context']
        self.assertEqual((len(context['history']),context['remaining_attempts']),(22,12))
    def test_schema_repair_continuation_reuses_measurements_and_global_request_count(self):
        import sys,copy
        import live_pilot,audit_live
        prior=self.root/'MOCK_FAILED_PHASE';target=self.root/'MOCK_CONTINUATION'
        clients=[MockExtendedShared('extra_fixed'),MockExtendedShared()]
        current={'root':None,'client':None,'evaluations':0}
        class FakeSimulator:
            def evaluate(self,point,origin,mode='corrected',export=False,refined=False):
                current['evaluations']+=1
                root=current['root'];number=len(list((root/'attempts').glob('[0-9]*')))+1
                result=observation('MOCK',point,origin)
                result.update(attempt=number,returncode=0,mode=mode,export=export,refined=refined)
                (root/'attempts'/f'{number:03d}').mkdir(parents=True)
                return result
        def freeze(args,module):
            args.root.mkdir();(args.root/'attempts').mkdir()
            (args.root/'protocol.json').write_text('{"mock_only":true}')
            current['root']=args.root;return FakeSimulator()
        class Factory:
            chat=MockExtendedShared.chat
            def __new__(cls,config):return current['client']
        shared=SimpleNamespace(load_config=lambda:None,Client=Factory)
        def audit(root):
            (root/'checks.json').write_text('{"api_cost_accounted_usd":"0.00165"}')
        def arguments(root,resume=None):return SimpleNamespace(root=root,resume_from=resume,shared_module=Path('MOCK_SHARED/openrouter_shared.py'),binary=Path('MOCK_NGSPICE'),selector=Path('MOCK_SELECTOR'))
        with patch.dict(sys.modules,{'openrouter_shared':shared}),patch.object(live_pilot,'freeze',freeze),patch.object(audit_live,'audit_preflight',lambda root:(root/'preflight_checks.json').write_text('{"passed":true,"mock_only":true}')),patch.object(audit_live,'audit',audit),patch('socket.socket',side_effect=AssertionError('Network forbidden')):
            current['client']=clients[0];live_pilot.run(arguments(prior))
            self.assertEqual((current['evaluations'],len(clients[0].calls)),(39,3))
            control_before=(prior/'fixed_gp_history.json').read_bytes()
            current['client']=clients[1];live_pilot.run(arguments(target,prior))
        result=json.loads((target/'execution_summary.json').read_text())
        self.assertEqual((current['evaluations'],result['spice_attempts']),(64,64))
        self.assertEqual((len(clients[1].calls),result['api_attempts']),(4,7))
        self.assertTrue(result['matched_budget'])
        self.assertEqual((target/'fixed_gp_history.json').read_bytes(),control_before)
        self.assertEqual((prior/'fixed_gp_history.json').read_bytes(),control_before)
    @unittest.skipUnless(os.environ.get('AUTOSIZER_SHARED_MODULE_PATH'),'Explicit read-only shared module source path not provided')
    def test_actual_installed_shared_contract_probe_never_reads_config(self):
        spec=importlib.util.spec_from_file_location('shared_interface_readonly',os.environ['AUTOSIZER_SHARED_MODULE_PATH'])
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        # In-memory public settings only. No load_config call or credential material.
        client=module.Client(SimpleNamespace(public_settings=lambda:{'chat_model':'google/gemini-2.5-flash'}),_transport=lambda *a:self.fail('No shared transport allowed'))
        with patch.object(module,'load_config',side_effect=AssertionError('Private config forbidden')):
            if 'request_options' not in inspect.signature(client.chat).parameters:
                with self.assertRaises(SharedInterfaceIncomplete):self.controller(client).check_interface()
            else:
                self.assertTrue(self.controller(client).check_interface())
                options=dict(CONFIG['request_template']);options.pop('model');options.pop('stream')
                normalized=module.normalize_request_options(options,'google/gemini-2.5-flash')
                self.assertEqual(normalized['provider']['only'],['google-ai-studio'])
                self.assertEqual(normalized['reasoning'],{'enabled':False})
                quote=module.conservative_chat_quote(self.messages('circuit_understanding'),1536,options)
                self.assertEqual(quote['reserved_cost_usd'],'0.32')


if __name__=='__main__':unittest.main()
