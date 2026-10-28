"""OpenAI-compatible completion adapter. No requests until caller explicitly enables network."""
import json,os,time,urllib.request,urllib.error
class ModelAPIError(RuntimeError): pass
class ChatAPI:
 def __init__(self,allow_network=False,transport=None):
  self.allow_network=allow_network;self.transport=transport or urllib.request.urlopen
 def complete(self,messages,max_tokens=640):
  if not self.allow_network: raise ModelAPIError('Network is not authorized')
  base=os.environ.get('PAPER_LLM_BASE_URL','').rstrip('/')
  key=os.environ.get('PAPER_LLM_API_KEY','');model=os.environ.get('PAPER_LLM_MODEL','')
  if not all([base,key,model]): raise ModelAPIError('Required runtime configuration missing')
  payload={'model':model,'messages':messages,'temperature':0,'max_tokens':max_tokens,'stream':False}
  data=json.dumps(payload).encode()
  if len(data)>18000: raise ModelAPIError('Request byte cap exceeded')
  request=urllib.request.Request(base+'/chat/completions',data=data,headers={'Content-Type':'application/json','Authorization':'Bearer '+key},method='POST')
  start=time.monotonic()
  try:
   with self.transport(request,timeout=180) as response: raw=response.read(1000001)
  except urllib.error.HTTPError as exc: raise ModelAPIError('Provider HTTP status '+str(exc.code)) from None
  except Exception as exc: raise ModelAPIError('Provider transport failed: '+type(exc).__name__) from None
  if len(raw)>1000000: raise ModelAPIError('Response size cap exceeded')
  try:
   result=json.loads(raw);content=result['choices'][0]['message']['content']
   if not isinstance(content,str): raise ValueError()
   usage=result.get('usage',{})
  except Exception: raise ModelAPIError('Provider response does not match completion schema') from None
  # Deliberate allowlist; no request object, auth header, full provider body or env.
  return {'raw_output':content,'usage':usage,'seconds':time.monotonic()-start,'model':result.get('model',model),'request_model':model,'max_tokens':max_tokens,'temperature':0}

