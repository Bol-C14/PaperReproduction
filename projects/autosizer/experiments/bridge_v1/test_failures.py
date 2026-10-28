"""Additional controller failure/stop tests; all responses synthetic, no network."""
from pathlib import Path
import json
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import bridge

class StopFixture(bridge.TestController):
    def call(self, *, stage,messages,**kwargs):
        if stage=='inner_iteration':return {'action':'stop','reasoning':'TEST ONLY: stop preserved'}
        return super().call(stage=stage,messages=messages,**kwargs)

class InvalidFixture(bridge.TestController):
    def call(self, *, stage,messages,**kwargs):
        result=super().call(stage=stage,messages=messages,**kwargs)
        if stage=='inner_iteration':result['n_samples']=13
        return result

class FailurePaths(unittest.TestCase):
    def test_stop_never_simulates(self):
        with tempfile.TemporaryDirectory() as tmp:
            sim=SimpleNamespace(root=Path(tmp),evaluate=lambda *a,**k:self.fail('No simulation allowed'))
            self.assertEqual(bridge.run_controller(sim,StopFixture()),[])
            decision=next((Path(tmp)/'test_controller').glob('call_*_inner_iteration'))
            self.assertEqual(json.loads((decision/'raw_response.json').read_text())['action'],'stop')
    def test_invalid_exact_batch_archived_before_simulation(self):
        with tempfile.TemporaryDirectory() as tmp:
            sim=SimpleNamespace(root=Path(tmp),evaluate=lambda *a,**k:self.fail('No simulation allowed'))
            with self.assertRaises(ValueError):bridge.run_controller(sim,InvalidFixture())
            decision=next((Path(tmp)/'test_controller').glob('call_*_inner_iteration'))
            self.assertEqual(json.loads((decision/'raw_response.json').read_text())['n_samples'],13)
            self.assertTrue((decision/'error.json').is_file())
    def test_api_schema_retry_local_stub_only(self):
        calls=[]
        def transport(*args):
            calls.append(1)
            response='not JSON' if len(calls)==1 else json.dumps({k:'TEST FIXTURE' for k in bridge.CU_FIELDS})
            return {'choices':[{'message':{'content':response}}]}
        # Clearly synthetic designated values, used by in-memory transport only.
        env={'PAPER_LLM_BASE_URL':'https://example.invalid','PAPER_LLM_API_KEY':'OFFLINE_FIXTURE_ONLY','PAPER_LLM_MODEL':'TEST_FIXTURE'}
        adapter=bridge.OpenAICompatibleController(authorized=True,transport=transport,environ=env)
        with tempfile.TemporaryDirectory() as tmp,patch('urllib.request.urlopen',side_effect=AssertionError('Network prohibited')):
            controller=bridge.APIBridgeController(adapter=adapter,authorized=True,token_counter=lambda messages:100,evidence_dir=tmp)
            controller.call(stage='circuit_understanding',messages=bridge.request('circuit_understanding',[]))
            self.assertEqual(adapter.calls,2)
            self.assertTrue((Path(tmp)/'call_01/bridge_validation_error.json').is_file())
    def test_token_cap_prevents_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter=SimpleNamespace(calls=0,call=lambda **k:self.fail('No transport allowed'))
            controller=bridge.APIBridgeController(adapter=adapter,authorized=True,token_counter=lambda messages:8193,evidence_dir=tmp)
            with self.assertRaises(ValueError):controller.call(stage='circuit_understanding',messages=bridge.request('circuit_understanding',[]))
    def test_total_call_cap_prevents_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter=SimpleNamespace(calls=10,call=lambda **k:self.fail('No transport allowed'))
            controller=bridge.APIBridgeController(adapter=adapter,authorized=True,token_counter=lambda messages:100,evidence_dir=tmp)
            with self.assertRaises(RuntimeError):controller.call(stage='circuit_understanding',messages=bridge.request('circuit_understanding',[]))

if __name__=='__main__':unittest.main()
