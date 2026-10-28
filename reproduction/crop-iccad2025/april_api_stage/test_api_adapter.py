import unittest,os,json,urllib.error
from unittest.mock import patch
from api_adapter import ChatAPI,ModelAPIError
class Response:
 def __init__(self,data): self.data=data
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,n):return self.data
class AdapterTests(unittest.TestCase):
 def test_default_blocks_before_config_or_transport(self):
  called=[]
  with self.assertRaisesRegex(ModelAPIError,'not authorized'):ChatAPI(transport=lambda *a,**k:called.append(1)).complete([])
  self.assertEqual(called,[])
 @patch.dict(os.environ,{'PAPER_LLM_BASE_URL':'https://example.invalid/v1','PAPER_LLM_API_KEY':'test-secret','PAPER_LLM_MODEL':'test-model'})
 def test_wire_schema_and_log_allowlist(self):
  def transport(req,timeout):
   self.assertEqual(req.full_url,'https://example.invalid/v1/chat/completions')
   self.assertEqual(req.get_header('Authorization'),'Bearer test-secret')
   p=json.loads(req.data);self.assertEqual(p['max_tokens'],640);self.assertFalse(p['stream'])
   return Response(json.dumps({'choices':[{'finish_reason':'stop','message':{'content':'{"configuration":{"mode":"fast","noalumacc":true}}'}}],'usage':{'prompt_tokens':5,'completion_tokens':8,'provider_secret':'omit'},'secret_provider_field':'omit'}).encode())
  result=ChatAPI(True,transport,token_counter=lambda m:10).complete([{'role':'user','content':'public RTL'}])
  self.assertNotIn('test-secret',json.dumps(result));self.assertNotIn('secret_provider_field',result);self.assertNotIn('provider_secret',result['usage'])
 @patch.dict(os.environ,{'PAPER_LLM_BASE_URL':'https://example.invalid/v1','PAPER_LLM_API_KEY':'test-secret','PAPER_LLM_MODEL':'test-model'})
 def test_http_errors_redact_body_and_url(self):
  def transport(req,timeout):raise urllib.error.HTTPError(req.full_url,401,'test-secret',{},None)
  with self.assertRaisesRegex(ModelAPIError,'HTTP status 401') as c:ChatAPI(True,transport,token_counter=lambda m:10).complete([])
  self.assertNotIn('test-secret',str(c.exception));self.assertNotIn('example.invalid',str(c.exception))
 @patch.dict(os.environ,{'PAPER_LLM_BASE_URL':'https://example.invalid/v1','PAPER_LLM_API_KEY':'test-secret','PAPER_LLM_MODEL':'test-model'})
 def test_budget_and_counter_fail_before_transport(self):
  called=[]
  for counter,kwargs in [(None,{}),(lambda m:4097,{}),(lambda m:10,{'max_tokens':641}),(lambda m:10,{'byte_cap':12000})]:
   with self.assertRaises(ModelAPIError):
    ChatAPI(True,lambda *a,**k:called.append(1),token_counter=counter).complete([{'role':'user','content':'x'*13000}],**kwargs)
  self.assertEqual(called,[])
 @patch.dict(os.environ,{'PAPER_LLM_BASE_URL':'https://example.invalid/v1','PAPER_LLM_API_KEY':'test-secret','PAPER_LLM_MODEL':'test-model'})
 def test_truncated_response_is_not_a_completed_generation(self):
  def transport(*a,**k):return Response(json.dumps({'choices':[{'finish_reason':'length','message':{'content':'{}'}}]}).encode())
  with self.assertRaisesRegex(ModelAPIError,'completed chat schema'):
   ChatAPI(True,transport,token_counter=lambda m:10).complete([])
 def test_explicit_openrouter_base_and_single_fixed_model(self):
  calls=[]
  def transport(req,timeout):
   calls.append(req)
   self.assertEqual(req.full_url,'https://openrouter.ai/api/v1/chat/completions')
   payload=json.loads(req.data)
   self.assertEqual(payload['model'],'test-provider/fixed-model-test-only')
   self.assertEqual(set(payload),{'model','messages','temperature','max_tokens','stream','provider'})
   self.assertEqual(payload['provider'],{'allow_fallbacks':False})
   self.assertNotIn('models',payload)
   return Response(json.dumps({'model':'test-provider/fixed-model-test-only','choices':[{'finish_reason':'stop','message':{'content':'{}'}}]}).encode())
  api=ChatAPI(True,transport,token_counter=lambda m:10,base_url='https://openrouter.ai/api/v1/',api_key='DUMMY-TEST-ONLY',model='test-provider/fixed-model-test-only')
  result=api.complete([{'role':'user','content':'public fixture only'}])
  self.assertEqual(len(calls),1)
  self.assertEqual(result['request_model'],'test-provider/fixed-model-test-only')
  self.assertIs(result['provider_fallbacks_requested'],False)
  self.assertNotIn('DUMMY-TEST-ONLY',json.dumps(result))
 def test_explicit_config_stays_fixed_when_process_environment_changes(self):
  calls=[]
  def transport(req,timeout):
   calls.append(req)
   self.assertEqual(req.full_url,'https://openrouter.ai/api/v1/chat/completions')
   self.assertEqual(json.loads(req.data)['model'],'test-provider/fixed-model-test-only')
   self.assertEqual(req.get_header('Authorization'),'Bearer DUMMY-TEST-ONLY')
   return Response(json.dumps({'choices':[{'finish_reason':'stop','message':{'content':'{}'}}]}).encode())
  api=ChatAPI(True,transport,token_counter=lambda m:10,base_url='https://openrouter.ai/api/v1',api_key='DUMMY-TEST-ONLY',model='test-provider/fixed-model-test-only')
  with patch.dict(os.environ,{'PAPER_LLM_BASE_URL':'https://example.invalid/changed','PAPER_LLM_API_KEY':'changed-test-only','PAPER_LLM_MODEL':'changed-test-model'}):
   api.complete([])
  self.assertEqual(len(calls),1)
 def test_http_and_transport_errors_never_trigger_hidden_retry(self):
  for kind in ('429','503','timeout'):
   calls=[]
   def transport(req,timeout):
    calls.append(1)
    if kind=='timeout':raise TimeoutError('dummy test timeout')
    raise urllib.error.HTTPError(req.full_url,int(kind),'dummy test error',{},None)
   api=ChatAPI(True,transport,token_counter=lambda m:10,base_url='https://openrouter.ai/api/v1',api_key='DUMMY-TEST-ONLY',model='test-provider/fixed-model-test-only')
   with self.assertRaises(ModelAPIError):api.complete([])
   self.assertEqual(calls,[1])
if __name__=='__main__': unittest.main()
