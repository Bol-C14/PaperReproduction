"""Opt-in future Chat transport. Import/approval validation never reads a secret.
Only an explicitly approved live run lazily reads NR_KEY at an actual admitted call.
No fallback key, discovery endpoint, redirects, SDK retries or secret diagnostics.
"""
import datetime as dt,json,os,ssl,threading,urllib.error,urllib.request
from pathlib import Path
from chat_adapter import BASE_URL,MODEL,SECRET_ENV,EXPIRES,LiveDisabled,Stopped

def validate_approval(path,*,now=None):
    if path is None:raise LiveDisabled('explicit parent approval file required')
    now=now or dt.datetime.now(dt.timezone.utc)
    a=json.loads(Path(path).read_text())
    if a.get('parent_approved') is not True or a.get('secret_injection_confirmed') is not True:raise LiveDisabled('parent activation/injection confirmation required')
    if a.get('domain_authorized')!='models.northern-relay.com' or a.get('model')!=MODEL:raise LiveDisabled('domain/model confirmation required')
    if a.get('fixture_only') is not True or a.get('accept_estimated_token_reservations') is not True:raise LiveDisabled('fixture and estimated-accounting scope must be accepted')
    end=dt.datetime.fromisoformat(a['expires_utc'].replace('Z','+00:00'))
    if end.tzinfo is None or end>EXPIRES or now+dt.timedelta(seconds=90)>=end:raise LiveDisabled('approval expired/outside credential lifetime')
    if a.get('total_token_ceiling')!=100000 or a.get('shared_concurrency')!=4:raise LiveDisabled('wrong experiment budget')
    return a

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

class LiveChatTransport:
    mode='live_chat_completions'
    def __init__(self,approval_path,*,key_supplier=None,clock=None):
        self.clock=clock or (lambda:dt.datetime.now(dt.timezone.utc))
        self.approval_path=approval_path;self.approval=validate_approval(approval_path,now=self.clock())
        self.key_supplier=key_supplier or (lambda:os.environ[SECRET_ENV]);self.network_attempts=0;self._request_lock=threading.Lock()
    def __call__(self,request,timeout):
        validate_approval(self.approval_path,now=self.clock())
        if request['url']!=BASE_URL+'/chat/completions' or request['json']['model']!=MODEL:raise Stopped('route/model mismatch')
        try:key=self.key_supplier()
        except KeyError:raise Stopped('NR_KEY is not injected; no request sent') from None
        if not isinstance(key,str) or not key:raise Stopped('NR_KEY unavailable; no request sent')
        # Key is never persisted or passed to a subprocess. Only the exact HTTPS route.
        opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        req=urllib.request.Request(request['url'],data=json.dumps(request['json']).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
        try:
            with self._request_lock:self.network_attempts+=1
            with opener.open(req,timeout=timeout) as response:
                raw=response.read(2*1024*1024+1)
                if len(raw)>2*1024*1024:raise Stopped('response byte ceiling')
                if key.encode() in raw:raise Stopped('credential echo refused; no response artifact retained')
                return response.status,{},json.loads(raw)
        except urllib.error.HTTPError as e:
            # Never return raw error text or redirect locations; preserve only Retry-After.
            return e.code,{'Retry-After':e.headers.get('Retry-After')},{}
