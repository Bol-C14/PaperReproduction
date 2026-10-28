"""Offline regressions only: synthetic supplier, mocked HTTP, forbidden sockets.
No real key lookup, network, model or EDA invocation. Tests never print fixtures.
"""
import datetime as dt,io,json,socket,tempfile,traceback,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
from chat_adapter import MODEL,EXPIRES,Stopped,build_request
from live_transport import LiveChatTransport,RESPONSE_REJECTED,TRANSPORT_FAILED
from runtime_accounting import Ledger,AccountedChat,usage_total
from run_canary import Canary
NOW=dt.datetime(2026,10,28,tzinfo=dt.timezone.utc)

def ordinary_body(content='Preserve carry and unchanged input ports.'):
    return {'choices':[{'message':{'content':content},'finish_reason':'stop'}],'usage':{'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}}

class Response:
    status=200
    def __init__(self,raw):self.raw=raw
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,n):return self.raw[:n]
class Opener:
    def __init__(self,raw=None,error=None):self.raw=raw;self.error=error
    def open(self,*args,**kwargs):
        if self.error is not None:raise self.error
        return Response(self.raw)
class NeverVerifier:
    rows=[]
    def __call__(self,*args,**kwargs):raise AssertionError('EDA must not execute in security tests')

class CredentialBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.secret='synthetic-'+'audit-credential'
        self.tmp=tempfile.TemporaryDirectory(prefix='t2s-client-security-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.approval=self.root/'approval.json'
        self.approval.write_text(json.dumps({'parent_approved':True,'secret_injection_confirmed':True,'domain_authorized':'models.northern-relay.com','model':MODEL,'fixture_only':True,'accept_estimated_token_reservations':True,'expires_utc':EXPIRES.isoformat(),'total_token_ceiling':100000,'shared_concurrency':4}))
        self.guard=patch.object(socket,'socket',side_effect=AssertionError('real network forbidden'));self.guard.start();self.addCleanup(self.guard.stop)
    def transport(self,supplier=None):
        t=LiveChatTransport(self.approval,key_supplier=supplier or (lambda:self.secret),clock=lambda:NOW)
        t.mode='offline_security_mock';return t
    def request(self):return build_request([{'role':'user','content':'public fixture task'}])
    def raw(self,obj,*,escaped=False):
        text=json.dumps(obj)
        if escaped:
            text=text.replace(self.secret,'\\u0073'+self.secret[1:])
            self.assertFalse(self.secret.encode() in text.encode(),'test must exercise post-decode protection')
        return text.encode()
    def reject(self,opener,*,supplier=None):
        with patch('live_transport.urllib.request.build_opener',return_value=opener):
            try:self.transport(supplier)(self.request(),30)
            except Stopped as exc:
                rendered=''.join(traceback.format_exception(type(exc),exc,exc.__traceback__))
                self.assertFalse(self.secret in str(exc) or self.secret in repr(exc) or self.secret in rendered,'credential in exception rendering')
                self.assertFalse(self.secret in repr(exc.__dict__),'credential in exception attributes')
                self.assertIsNone(exc.__cause__);self.assertIsNone(exc.__context__)
                return str(exc)
        self.fail('credential-bearing or unsafe response escaped transport')
    def test_plain_echo_rejected(self):
        self.assertEqual(self.reject(Opener(self.raw(ordinary_body(self.secret)))),RESPONSE_REJECTED)
    def test_unicode_escaped_echo_rejected(self):
        self.assertEqual(self.reject(Opener(self.raw(ordinary_body(self.secret),escaped=True))),RESPONSE_REJECTED)
    def test_nested_unused_reasoning_and_dictionary_keys(self):
        for extension in [ {'reasoning_content':self.secret}, {'extension':[{'deep':{'value':'prefix '+self.secret+' suffix'}}]}, {'extension':{self.secret:'unused value'}} ]:
            with self.subTest(location=list(extension)):
                obj=ordinary_body();obj.update(extension)
                self.assertEqual(self.reject(Opener(self.raw(obj,escaped=True))),RESPONSE_REJECTED)
    def test_top_level_dictionary_key(self):
        obj=ordinary_body();obj[self.secret]='unused'
        self.assertEqual(self.reject(Opener(self.raw(obj,escaped=True))),RESPONSE_REJECTED)
    def test_http_error_decoded_nested_echo_rejected(self):
        for code in [400,401,429,500]:
            error=urllib.error.HTTPError('https://models.northern-relay.com/v1/chat/completions',code,'provider error',{'Retry-After':'1'},io.BytesIO(self.raw({'error':{'nested':[self.secret]}},escaped=True)))
            with self.subTest(status=code):self.assertEqual(self.reject(Opener(error=error)),RESPONSE_REJECTED)
    def test_credential_bearing_retry_header_rejected(self):
        error=urllib.error.HTTPError('https://models.northern-relay.com/v1/chat/completions',429,'provider error',{'Retry-After':self.secret},io.BytesIO(b'{}'))
        self.assertEqual(self.reject(Opener(error=error)),RESPONSE_REJECTED)
    def test_invalid_opaque_retry_header_not_returned(self):
        header='\\u0073'+self.secret[1:]
        error=urllib.error.HTTPError('https://models.northern-relay.com/v1/chat/completions',429,'provider error',{'Retry-After':header},io.BytesIO(b'{}'))
        with patch('live_transport.urllib.request.build_opener',return_value=Opener(error=error)):
            status,headers,body=self.transport()(self.request(),30)
        self.assertEqual(status,429);self.assertEqual(headers,{'Retry-After':None});self.assertEqual(body,{})
    def test_normal_json_and_retry_controls_unchanged(self):
        payload=ordinary_body()
        with patch('live_transport.urllib.request.build_opener',return_value=Opener(self.raw(payload))):
            self.assertEqual(self.transport()(self.request(),30),(200,{},payload))
        for retry in ['1','Wed, 28 Oct 2026 00:00:03 GMT']:
            error=urllib.error.HTTPError('https://models.northern-relay.com/v1/chat/completions',429,self.secret,{'Retry-After':retry},io.BytesIO(b'<html>busy</html>'))
            with patch('live_transport.urllib.request.build_opener',return_value=Opener(error=error)):
                self.assertEqual(self.transport()(self.request(),30),(429,{'Retry-After':retry},{}))
    def test_sensitive_transport_exception_is_fixed_and_unchained(self):
        self.assertEqual(self.reject(Opener(error=TimeoutError(self.secret))),TRANSPORT_FAILED)
    def test_sensitive_supplier_exception_is_fixed_and_unchained(self):
        def supplier():raise RuntimeError(self.secret)
        self.assertEqual(self.reject(Opener(b'{}'),supplier=supplier),'NR_KEY unavailable; no request sent')
    def test_malformed_json_exception_does_not_retain_document(self):
        raw=self.raw(ordinary_body(self.secret),escaped=True)[:-1]
        self.assertEqual(self.reject(Opener(raw)),RESPONSE_REJECTED)
    def test_sensitive_error_read_exception_is_fixed(self):
        secret=self.secret
        class BrokenBody(io.BytesIO):
            def read(self,*args):raise OSError(secret)
        error=urllib.error.HTTPError('https://models.northern-relay.com/v1/chat/completions',500,'provider error',{},BrokenBody())
        self.assertEqual(self.reject(Opener(error=error)),RESPONSE_REJECTED)
    def test_sensitive_error_close_exception_is_fixed(self):
        secret=self.secret
        class BrokenClose(urllib.error.HTTPError):
            already_closed=False
            def close(self):
                if not self.already_closed:
                    self.already_closed=True;super().close();raise OSError(secret)
        error=BrokenClose('https://models.northern-relay.com/v1/chat/completions',429,'provider error',{'Retry-After':'1'},io.BytesIO(b'{}'))
        self.assertEqual(self.reject(Opener(error=error)),RESPONSE_REJECTED)
    def test_decoded_echo_never_reaches_artifact_or_hash_sink(self):
        for purpose in ['mutation','reflection','generation']:
            out=self.root/purpose;transport=self.transport();chat=AccountedChat(transport,Ledger(clock=lambda:NOW));canary=Canary(chat,NeverVerifier(),out)
            with patch('live_transport.urllib.request.build_opener',return_value=Opener(self.raw(ordinary_body(self.secret),escaped=True))),patch('run_canary.sha') as hasher:
                try:canary.call(purpose,'fixed','security-probe','public fixture only')
                except Stopped:pass
                else:self.fail('response escaped into canary')
                self.assertEqual(hasher.call_count,0,'rejected response must not reach hash sink')
            for f in out.iterdir():
                self.assertFalse(self.secret in f.read_text(),'credential persisted in artifact')
            report=json.loads((out/'report.json').read_text());self.assertEqual(report['validated_skill_state'],{});self.assertEqual(report['validated_lessons'],{});self.assertEqual(report['budget']['active'],0)
            self.assertFalse(any(f.suffix=='.sv' for f in out.iterdir()),'rejected RTL must not be written')
    def test_placeholder_guarantee_is_only_exact_injected_value(self):
        self.secret='synthetic-'+'network-placeholder'
        self.assertEqual(self.reject(Opener(self.raw({'nested':[self.secret]},escaped=True))),RESPONSE_REJECTED)
        # Deliberately different, unknown strings are not promised to be secrets.
        safe={'metadata':'unrelated ordinary text'}
        with patch('live_transport.urllib.request.build_opener',return_value=Opener(self.raw(safe))):self.assertEqual(self.transport()(self.request(),30),(200,{},safe))

class UsageProtocolTests(unittest.TestCase):
    def setUp(self):self.guard=patch.object(socket,'socket',side_effect=AssertionError('real network forbidden'));self.guard.start();self.addCleanup(self.guard.stop)
    def test_non_dictionary_usage_is_unknown(self):
        for value in [None,[],[1],'usage',0,False,3.5]:
            with self.subTest(usage_type=type(value).__name__):self.assertIsNone(usage_total({'usage':value}))
    def test_malformed_and_truncated_with_unknown_usage_finish_once(self):
        cases=[[],[{'message':{'content':'ordinary text'},'finish_reason':'length'}],None]
        for usage in [None,[],'usage']:
            for choices in cases:
                with self.subTest(usage_type=type(usage).__name__,choices_type=type(choices).__name__):
                    class Mock:
                        mode='offline_security_mock';calls=0
                        def __call__(self,*args,**kwargs):self.calls+=1;return 200,{}, {'choices':choices,'usage':usage}
                    transport=Mock();ledger=Ledger(clock=lambda:NOW);chat=AccountedChat(transport,ledger)
                    with patch.object(ledger,'finish',wraps=ledger.finish) as finish:
                        with self.assertRaises(Stopped):chat.call(build_request([{'role':'user','content':'public fixture'}]),arm='fixed',purpose='generation',rollout='security')
                    snap=ledger.snapshot();self.assertEqual(finish.call_count,1);self.assertEqual(transport.calls,1);self.assertEqual(snap['active'],0);self.assertEqual(snap['settled_known_plus_conservative_unknown_tokens'],snap['cumulative_admission_reservations']);self.assertNotEqual(snap['rows'][0]['status'],'in_flight');self.assertFalse(snap['rows'][0]['usage_known'])
    def test_valid_choices_with_null_usage_remains_usable_and_charged(self):
        class Mock:
            mode='offline_security_mock'
            def __call__(self,*args,**kwargs):payload=ordinary_body();payload['usage']=None;return 200,{},payload
        ledger=Ledger(clock=lambda:NOW);chat=AccountedChat(Mock(),ledger);text=chat.call(build_request([{'role':'user','content':'fixture'}]),arm='fixed',purpose='generation',rollout='control')
        self.assertEqual(text,ordinary_body()['choices'][0]['message']['content']);self.assertEqual(ledger.charged,6144);self.assertEqual(ledger.snapshot()['active'],0)
    def test_retry_sleep_exception_does_not_double_finish(self):
        class Mock:
            mode='offline_security_mock';calls=0
            def __call__(self,*args,**kwargs):self.calls+=1;return 429,{'Retry-After':'0'},{'usage':None}
        def sleep(_):raise RuntimeError('synthetic sleep failure')
        ledger=Ledger(clock=lambda:NOW);transport=Mock();chat=AccountedChat(transport,ledger,sleep=sleep)
        with patch.object(ledger,'finish',wraps=ledger.finish) as finish:
            with self.assertRaises(Stopped):chat.call(build_request([{'role':'user','content':'fixture'}]),arm='fixed',purpose='generation',rollout='retry')
        self.assertEqual(finish.call_count,1);self.assertEqual(transport.calls,1);self.assertEqual(ledger.snapshot()['active'],0);self.assertEqual(ledger.rows[0]['status'],'429_retry');self.assertEqual(ledger.charged,6144)

if __name__=='__main__':unittest.main(verbosity=2)
