import datetime as dt,json,socket,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from chat_adapter import Limits,EXPIRES,MODEL,Stopped,LiveDisabled,build_request
from runtime_accounting import Ledger,AccountedChat,conservative_count,usage_total
from live_transport import validate_approval,LiveChatTransport,NoRedirect
from isolated_verifier import candidate_source
from run_canary import GOOD,BAD,MockChat,clean_skill
NOW=dt.datetime(2026,10,28,tzinfo=dt.timezone.utc)
def body(content=GOOD,total=15):return {'choices':[{'message':{'content':content},'finish_reason':'stop'}],'usage':{'prompt_tokens':total-5,'completion_tokens':5,'total_tokens':total}}
class Mock:
 mode='offline_mock_test'
 def __init__(self,*events):self.events=list(events);self.calls=0
 def __call__(self,r,timeout):
  self.calls+=1;e=self.events.pop(0)
  if isinstance(e,Exception):raise e
  return e
class RuntimeTests(unittest.TestCase):
 def setUp(self):self.net=patch.object(socket,'socket',side_effect=AssertionError('network forbidden'));self.net.start();self.addCleanup(self.net.stop)
 def req(self):return build_request([{'role':'user','content':'fixture task'}],max_tokens=32)
 def client(self,*events,limits=Limits(),clock=lambda:NOW):return AccountedChat(Mock(*events),Ledger(limits,clock=clock),sleep=lambda _:None)
 def call(self,c,arm='fixed'):return c.call(self.req(),arm=arm,purpose='generation',rollout='test')
 def test_usage_settlement_keeps_admission_reservation(self):
  c=self.client((200,{},body()));self.call(c);s=c.ledger.snapshot();self.assertEqual(s['cumulative_admission_reservations'],6144);self.assertEqual(s['settled_known_plus_conservative_unknown_tokens'],15)
 def test_unknown_usage_full_charge_but_text_usable(self):
  b=body();b.pop('usage');c=self.client((200,{},b));self.assertEqual(self.call(c),GOOD);self.assertEqual(c.ledger.charged,6144);self.assertFalse(c.ledger.rows[0]['usage_known'])
 def test_inconsistent_usage_unknown_full_charge(self):
  b=body();b['usage']['total_tokens']=999;c=self.client((200,{},b));self.call(c);self.assertEqual(c.ledger.charged,6144)
 def test_usage_over_estimate_halts(self):
  c=self.client((200,{},body(total=7000)))
  with self.assertRaises(Stopped):self.call(c)
  self.assertTrue(c.ledger.halted);self.assertEqual(c.ledger.charged,7000)
 def test_unknown_timeout_no_retry_no_error_text(self):
  c=self.client(TimeoutError('secret-looking error should never be logged'),(200,{},body()))
  with self.assertRaises(Stopped):self.call(c)
  self.assertEqual(c.transport.calls,1);self.assertEqual(c.ledger.charged,6144);self.assertNotIn('secret-looking',json.dumps(c.ledger.snapshot()))
 def test_429_each_attempt_charged_and_usage_settled(self):
  c=self.client((429,{'Retry-After':'0'},{}),(200,{},body()));self.call(c);self.assertEqual(c.ledger.reserved,12288);self.assertEqual(c.ledger.charged,6159)
 def test_429_never_reuses_previous_body_on_timeout(self):
  c=self.client((429,{'Retry-After':'0'},body()),TimeoutError())
  with self.assertRaises(Stopped):self.call(c)
  self.assertFalse(c.ledger.rows[1]['usage_known']);self.assertEqual(c.ledger.rows[1]['charged_tokens'],6144)
 def test_auth_halts_other_arm_new_calls(self):
  c=self.client((401,{},{}),(200,{},body()))
  with self.assertRaises(Stopped):self.call(c)
  with self.assertRaises(Stopped):self.call(c,'evolution')
  self.assertEqual(c.transport.calls,1)
 def test_expiry_prevents_transport(self):
  c=self.client(clock=lambda:EXPIRES)
  with self.assertRaises(Stopped):self.call(c)
  self.assertEqual(c.transport.calls,0)
 def test_equal_per_arm_reservation_ceiling(self):
  c=self.client(*[(200,{},body())]*9)
  for _ in range(8):self.call(c)
  with self.assertRaises(Stopped):self.call(c)
  self.assertEqual(c.ledger.arm_reserved['fixed'],49152);self.call(c,'evolution');self.assertEqual(c.ledger.rows[-1]['arm'],'evolution')
 def test_global_four_active_limit(self):
  ledger=Ledger(clock=lambda:NOW)
  for _ in range(4):ledger.begin(self.req()['json'],'fixed','generation','test',1)
  with self.assertRaises(Stopped):ledger.begin(self.req()['json'],'evolution','generation','test',1)
  for i in range(4):ledger.finish(i,status='unknown')
 def test_admission_callback_before_transport(self):
  c=self.client((200,{},body()));seen=[];c.on_change=lambda:seen.append(c.transport.calls);self.call(c);self.assertEqual(seen,[0])
 def test_estimate_counts_utf8_not_characters(self):
  self.assertGreater(conservative_count({'text':'汉字'}),conservative_count({'text':'ab'}))
 def test_reasoning_details_not_double_counted(self):
  b=body();b['usage']['completion_tokens_details']={'reasoning_tokens':3};self.assertEqual(usage_total(b),15)
 def test_redaction_ledger_has_no_source_or_prompts(self):
  c=self.client((200,{},body(content='sensitive synthetic text')));self.call(c);self.assertNotIn('sensitive synthetic',json.dumps(c.ledger.snapshot()));self.assertNotIn('fixture task',json.dumps(c.ledger.snapshot()))
 def test_static_rtl_gate_blocks_side_effects(self):
  for src in [GOOD+' initial $finish;',GOOD+' `include "x"',GOOD+' // NR_KEY', 'not a module']:
   with self.assertRaises(ValueError):candidate_source(src)
  self.assertIn('module adder',candidate_source('```systemverilog\n'+GOOD+'\n```'))
 def test_skill_gate_blocks_sensitive_text(self):
  with self.assertRaises(ValueError):clean_skill('Bearer synthetic-not-a-credential')
 def approval(self,p):
  a={'parent_approved':True,'secret_injection_confirmed':True,'domain_authorized':'models.northern-relay.com','model':MODEL,'fixture_only':True,'accept_estimated_token_reservations':True,'expires_utc':EXPIRES.isoformat(),'total_token_ceiling':100000,'shared_concurrency':4};p.write_text(json.dumps(a));return a
 def test_approval_no_secret_access(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'approval.json';self.approval(p);supplier=[];transport=LiveChatTransport(p,key_supplier=lambda:supplier.append(True),clock=lambda:NOW);self.assertEqual(supplier,[]);self.assertEqual(transport.network_attempts,0)
 def test_missing_approval_blocks_before_supplier(self):
  with self.assertRaises((OSError,LiveDisabled)):LiveChatTransport(None,key_supplier=lambda:(_ for _ in ()).throw(AssertionError('must not read')),clock=lambda:NOW)
 def test_wrong_domain_or_expired_approval(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a';a=self.approval(p);a['domain_authorized']='example.com';p.write_text(json.dumps(a))
   with self.assertRaises(LiveDisabled):validate_approval(p,now=NOW)
   self.approval(p)
   with self.assertRaises(LiveDisabled):validate_approval(p,now=EXPIRES)
 def test_redirects_are_not_followed(self):self.assertIsNone(NoRedirect().redirect_request(None,None,302,None,None,None))
 def test_malformed_choices_still_settles_reported_usage(self):
  b=body();b['choices']=[];c=self.client((200,{},b))
  with self.assertRaises(Stopped):self.call(c)
  self.assertEqual(c.ledger.charged,15);self.assertTrue(c.ledger.rows[0]['usage_known'])
 def test_wrong_live_route_never_asks_for_key(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a';self.approval(p);read=[];t=LiveChatTransport(p,key_supplier=lambda:read.append(True),clock=lambda:NOW);r=self.req();r['url']='https://example.com/v1/chat/completions'
   with self.assertRaises(Stopped):t(r,30)
   self.assertEqual(read,[]);self.assertEqual(t.network_attempts,0)
 def test_synthetic_credential_echo_rejected_without_artifact(self):
  # Inject a synthetic test string; never read a real key or open a socket.
  class Response:
   status=200
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,n):return json.dumps(body(content='synthetic-test-credential')).encode()
  class Opener:
   def open(self,request,timeout):return Response()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a';self.approval(p);t=LiveChatTransport(p,key_supplier=lambda:'synthetic-test-credential',clock=lambda:NOW)
   with patch('live_transport.urllib.request.build_opener',return_value=Opener()):
    with self.assertRaises(Stopped) as e:t(self.req(),30)
   self.assertNotIn('synthetic-test-credential',str(e.exception))

if __name__=='__main__':unittest.main(verbosity=2)
