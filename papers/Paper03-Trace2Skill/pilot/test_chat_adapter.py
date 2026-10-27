import datetime as dt
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from chat_adapter import *

NOW=dt.datetime(2026,10,27,19,tzinfo=dt.timezone.utc)
def response(*,finish='stop',calls=None,usage=None,content='module dut; endmodule'):
    return {'choices':[{'message':{'content':content,'tool_calls':calls or [],'reasoning_content':'private mock reasoning not for logs'},'finish_reason':finish}], 'usage':usage or {'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}}
class Mock:
    mode='offline_mock'
    def __init__(self,*events):self.events=list(events);self.seen=[]
    def __call__(self,request,timeout):
        self.seen.append((request,timeout))
        event=self.events.pop(0)
        if isinstance(event,Exception):raise event
        return event
class TestAdapter(unittest.TestCase):
    def setUp(self):self.network=patch.object(socket,'socket',side_effect=AssertionError('real network prohibited'));self.network.start();self.addCleanup(self.network.stop)
    def client(self,*events,limits=Limits(),clock=lambda:NOW,counter=lambda _:10,sleep=lambda _:None):
        mock=Mock(*events);return OfflineClient(mock,Budget(limits,clock=clock),counter=counter,sleep=sleep)
    def req(self):return build_request([{'role':'user','content':'Fix the visible RTL.'}],max_tokens=32)
    def call(self,c,**kwargs):return c.call(self.req(),purpose='generation',arm='fixed',rollout='r0',**kwargs)
    def test_chat_endpoint_and_exact_model(self):
        r=self.req();self.assertEqual(r['url'],BASE_URL+'/chat/completions');self.assertEqual(r['json']['model'],MODEL);self.assertFalse(r['json']['stream']);self.assertEqual(r['json']['n'],1)
    def test_success_usage(self):
        c=self.client((200,{},response()));r=self.call(c);self.assertEqual(r['usage']['total_tokens'],15);self.assertEqual(c.budget.tokens,42);self.assertEqual(c.budget.requests,1)
    def test_no_live_transport(self):
        with self.assertRaises(LiveDisabled):OfflineClient(lambda:None,Budget(clock=lambda:NOW))
    def test_live_entry_fails_closed(self):
        c=self.client()
        with self.assertRaises(LiveDisabled):c.send_live()
        self.assertEqual(c.transport.seen,[])
    def test_missing_tokenizer_stops_before_transport(self):
        c=self.client(counter=None)
        with self.assertRaises(Stopped):self.call(c)
        self.assertFalse(c.transport.seen)
    def test_expired_stops_before_transport(self):
        c=self.client(clock=lambda:EXPIRES)
        with self.assertRaises(Stopped):self.call(c)
        self.assertFalse(c.transport.seen)
    def test_expiry_safety_margin(self):
        c=self.client(clock=lambda:EXPIRES-dt.timedelta(seconds=89))
        with self.assertRaises(Stopped):self.call(c)
    def test_total_token_budget(self):
        c=self.client((200,{},response()),limits=Limits(tokens=41))
        with self.assertRaises(Stopped):self.call(c)
        self.assertEqual(c.budget.requests,0)
    def test_request_ceiling(self):
        c=self.client((200,{},response()),limits=Limits(requests=1));self.call(c)
        with self.assertRaises(Stopped):self.call(c)
    def test_rpm_window(self):
        c=self.client((200,{},response()),limits=Limits(rpm=1));self.call(c)
        with self.assertRaises(Stopped):self.call(c)
    def test_tpm_window(self):
        c=self.client((200,{},response()),limits=Limits(tpm=41))
        with self.assertRaises(Stopped):self.call(c)
    def test_single_concurrency_gate(self):
        b=Budget(Limits(concurrency=1),clock=lambda:NOW);b.begin(1)
        with self.assertRaises(Stopped):b.begin(1)
        b.end();b.begin(1);b.end()
    def test_reject_broadened_limits(self):
        for limits in [Limits(concurrency=5),Limits(tokens=100001),Limits(rpm=61),Limits(tpm=500001),Limits(max_attempts=3)]:
            with self.assertRaises(ValueError):Budget(limits,clock=lambda:NOW)
    def test_auth_failure_halts_all_later_calls(self):
        for status in (401,403):
            c=self.client((status,{}, {'error':'synthetic sensitive error text'}),(200,{},response()))
            with self.assertRaises(Stopped):self.call(c)
            with self.assertRaises(Stopped):self.call(c)
            self.assertEqual(len(c.transport.seen),1);self.assertNotIn('sensitive',json.dumps(c.audit))
    def test_429_numeric_wait_and_finite_retry(self):
        waits=[];c=self.client((429,{'Retry-After':'2'},{}),(200,{},response()),sleep=waits.append);self.call(c)
        self.assertEqual(waits,[2]);self.assertEqual(c.budget.requests,2);self.assertEqual(c.budget.tokens,84)
    def test_429_date_wait(self):
        date=email.utils.format_datetime(NOW+dt.timedelta(seconds=3));self.assertEqual(retry_after(date,NOW),3)
    def test_429_long_wait_stops_without_early_retry(self):
        waits=[];c=self.client((429,{'Retry-After':'120'},{}),sleep=waits.append)
        with self.assertRaises(Stopped):self.call(c)
        self.assertEqual(waits,[]);self.assertEqual(len(c.transport.seen),1)
    def test_429_missing_header_stops(self):
        c=self.client((429,{},{}))
        with self.assertRaises(Stopped):self.call(c)
        self.assertEqual(len(c.transport.seen),1)
    def test_429_retry_ceiling(self):
        c=self.client((429,{'Retry-After':'0'},{}),(429,{'Retry-After':'0'},{}),(200,{},response()))
        with self.assertRaises(Stopped):self.call(c)
        self.assertEqual(len(c.transport.seen),2)
    def test_429_expiry_before_retry(self):
        clock_values=iter([NOW,NOW,NOW,EXPIRES-dt.timedelta(seconds=95),EXPIRES-dt.timedelta(seconds=95)])
        # A fixed near-expiry clock admits first request but refuses wait+request margin.
        c=self.client((429,{'Retry-After':'10'},{}),clock=lambda:EXPIRES-dt.timedelta(seconds=95))
        with self.assertRaises(Stopped):self.call(c)
        self.assertEqual(len(c.transport.seen),1)
    def test_transport_timeout_is_uncertain_no_retry(self):
        c=self.client(TimeoutError('synthetic do-not-log timeout detail'),(200,{},response()))
        with self.assertRaises(Stopped):self.call(c)
        self.assertEqual(c.budget.requests,1);self.assertTrue(c.budget.halted);self.assertNotIn('do-not-log',json.dumps(c.audit))
    def test_server_failure_no_retry(self):
        c=self.client((500,{},{}),(200,{},response()))
        with self.assertRaises(Stopped):self.call(c)
        self.assertEqual(len(c.transport.seen),1)
    def test_missing_usage_keeps_reservation(self):
        body=response();body.pop('usage');c=self.client((200,{},body))
        with self.assertRaises(Stopped):self.call(c)
        self.assertEqual(c.budget.tokens,42)
    def test_usage_over_reservation_halts(self):
        c=self.client((200,{},response(usage={'prompt_tokens':100,'completion_tokens':5,'total_tokens':105})))
        with self.assertRaises(Stopped):self.call(c)
        self.assertTrue(c.budget.halted)
    def test_length_no_implicit_repair(self):
        c=self.client((200,{},response(finish='length')))
        with self.assertRaises(Stopped):self.call(c)
        self.assertEqual(len(c.transport.seen),1)
    def test_chat_tool_call_roundtrip(self):
        calls=[{'id':'t1','type':'function','function':{'name':'iverilog','arguments':'{"args":"dut.v"}'}}]
        c=self.client((200,{},response(finish='tool_calls',calls=calls,content=None)));r=self.call(c,allowed_tools=['iverilog']);self.assertEqual(r['tool_calls'][0]['arguments'],{'args':'dut.v'})
        m=[{'role':'assistant','content':None,'tool_calls':calls},{'role':'tool','tool_call_id':'t1','content':'compile ok'}]
        self.assertEqual(build_request(m)['json']['messages'],m)
    def test_unknown_tools_and_malformed_arguments(self):
        for name,args in [('shell','{}'),('iverilog','not-json'),('iverilog','[]')]:
            b=response(finish='tool_calls',calls=[{'id':'t','type':'function','function':{'name':name,'arguments':args}}])
            with self.assertRaises(Stopped):parse_response(b,['iverilog'])
    def test_no_parallel_tools(self):
        call={'id':'t','type':'function','function':{'name':'iverilog','arguments':'{}'}}
        with self.assertRaises(Stopped):parse_response(response(finish='tool_calls',calls=[call,call]),['iverilog'])
    def test_input_schema_rejects_responses_role_or_fields(self):
        with self.assertRaises(ValueError):build_request([{'role':'developer','content':'text'}])
        with self.assertRaises(ValueError):build_request([{'role':'user','content':'text','reasoning':'x'}])
        with self.assertRaises(ValueError):build_request([{'role':'tool','content':'text'}])
    def test_redacted_audit_has_no_text_or_reasoning(self):
        c=self.client((200,{},response(content='synthetic confidential RTL')));self.call(c);s=json.dumps(c.audit)
        for marker in ['Fix the visible','confidential','private mock reasoning','Authorization','api_key','messages']:self.assertNotIn(marker,s)
    def test_all_call_purposes_logged(self):
        c=self.client(*[(200,{},response())]*5)
        for p in ['generation','repair','reflection','mutation','compression']:c.call(self.req(),purpose=p,arm='interface_test',rollout='r0')
        self.assertEqual(len(c.audit),5);self.assertTrue(all(x['mode']=='offline_mock' and 'elapsed_seconds' in x for x in c.audit))
    def test_worker_environment_and_actual_child_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            env=worker_environment(Path(d));self.assertNotIn('NR_KEY',env);self.assertNotIn('HTTPS_PROXY',env)
            with patch.dict(os.environ,{'FAKE_CANARY_SECRET':'synthetic-only'}):
                out=subprocess.check_output([sys.executable,'-I','-c','import os,json; print(json.dumps({"fake": "FAKE_CANARY_SECRET" in os.environ, "nr": "NR_KEY" in os.environ}))'],env=env,text=True)
            self.assertEqual(json.loads(out),{'fake':False,'nr':False})

    def test_shared_controller_caps_roles_together(self):
        control=ExperimentController(clock=lambda:NOW)
        a=control.offline_client(Mock((200,{},response())),counter=lambda _:10)
        b=control.offline_client(Mock((200,{},response())),counter=lambda _:10)
        self.call(a);self.call(b)
        self.assertIs(a.budget,b.budget);self.assertEqual(control.budget.requests,2)
    def test_four_shared_leases_fifth_rejected(self):
        control=ExperimentController(clock=lambda:NOW)
        for _ in range(4):control.budget.begin(1)
        with self.assertRaises(Stopped):control.budget.begin(1)
        for _ in range(4):control.budget.end()
        self.assertEqual(control.budget.active,0)
    def test_threaded_roles_share_four_concurrency_without_api(self):
        import concurrent.futures
        control=ExperimentController(clock=lambda:NOW);entered=threading.Barrier(5);release=threading.Event()
        def hold():
            control.budget.begin(1);entered.wait(timeout=5);release.wait(timeout=5);control.budget.end()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures=[pool.submit(hold) for _ in range(4)];entered.wait(timeout=5)
            self.assertEqual(control.budget.active,4)
            with self.assertRaises(Stopped):control.budget.begin(1)
            release.set()
            for f in futures:f.result(timeout=5)
        self.assertEqual(control.budget.active,0)
    def test_retry_releases_exactly_one_lease(self):
        control=ExperimentController(clock=lambda:NOW);control.budget.begin(1)
        client=control.offline_client(Mock((429,{'Retry-After':'0'},{}),(200,{},response())),counter=lambda _:10)
        self.call(client);self.assertEqual(control.budget.active,1);control.budget.end()

    def test_new_secret_name_only_and_no_lookup_fallback(self):
        self.assertEqual(SECRET_ENV,'NR_KEY')
        import ast
        import chat_adapter
        tree=ast.parse(Path(chat_adapter.__file__).read_text())
        # Offline adapter has no environment reads at all, including no legacy fallback.
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in {'environ','getenv'} for n in ast.walk(tree)))
        self.assertNotIn('NR_KEY',worker_environment(Path('/tmp')))

if __name__=='__main__':unittest.main(verbosity=2)
