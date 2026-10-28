"""Opt-in future Chat transport. Import/approval validation never reads a secret.
Only an explicitly approved live run lazily reads NR_KEY at an actual admitted call.
No fallback key, discovery endpoint, redirects, SDK retries or secret diagnostics.
"""
import datetime as dt,json,os,ssl,threading,urllib.error,urllib.request
from pathlib import Path
from chat_adapter import BASE_URL,MODEL,SECRET_ENV,EXPIRES,LiveDisabled,Stopped,retry_after

RESPONSE_REJECTED='response rejected; no response artifact retained'
TRANSPORT_FAILED='transport failed; no response artifact retained'
MAX_RESPONSE_BYTES=2*1024*1024

def reject_credential_echo(value,key):
    """Check decoded JSON strings, including keys/unused provider fields.
    This covers the exact injected value, not arbitrary transforms or an unknown
    vault value when the process receives only a Network-secret placeholder.
    """
    pending=[value]
    while pending:
        item=pending.pop()
        if isinstance(item,str):
            if key in item:raise Stopped(RESPONSE_REJECTED)
        elif isinstance(item,dict):
            pending.extend(item.keys());pending.extend(item.values())
        elif isinstance(item,list):pending.extend(item)

def decode_checked_response(raw,key,*,allow_non_json=False):
    if not isinstance(raw,bytes) or len(raw)>MAX_RESPONSE_BYTES:raise Stopped(RESPONSE_REJECTED)
    if key.encode() in raw:raise Stopped(RESPONSE_REJECTED)
    decode_failed=False
    try:decoded=json.loads(raw)
    except (ValueError,UnicodeError,RecursionError):decode_failed=True
    if decode_failed:
        if allow_non_json:return None
        raise Stopped(RESPONSE_REJECTED)
    reject_credential_echo(decoded,key)
    return decoded

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
        supplier_error=None
        try:key=self.key_supplier()
        except KeyError:supplier_error='NR_KEY is not injected; no request sent'
        except Exception:supplier_error='NR_KEY unavailable; no request sent'
        if supplier_error:raise Stopped(supplier_error)
        if not isinstance(key,str) or not key:raise Stopped('NR_KEY unavailable; no request sent')
        # Key is never persisted or passed to a subprocess. Only the exact HTTPS route.
        result=None;http_error=None;rejected=False;failed=False
        try:
            opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
            req=urllib.request.Request(request['url'],data=json.dumps(request['json']).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
            with self._request_lock:self.network_attempts+=1
            with opener.open(req,timeout=timeout) as response:
                result=(response.status,{},decode_checked_response(response.read(MAX_RESPONSE_BYTES+1),key))
        except urllib.error.HTTPError as e:
            http_error=e
        except Stopped:rejected=True
        except Exception:failed=True
        # Raise outside except blocks: do not retain sensitive third-party error
        # messages/documents in __context__ or __cause__ exposed to direct callers.
        if rejected:raise Stopped(RESPONSE_REJECTED)
        if failed:raise Stopped(TRANSPORT_FAILED)
        if http_error is not None:
            try:
                decode_checked_response(http_error.read(MAX_RESPONSE_BYTES+1),key,allow_non_json=True)
                headers={'Retry-After':(http_error.headers or {}).get('Retry-After')}
                reject_credential_echo(headers,key)
                # Opaque invalid headers have no retry semantics; never propagate
                # their text to a direct caller (valid numbers/dates stay intact).
                if headers['Retry-After'] is not None:
                    try:retry_after(headers['Retry-After'],self.clock())
                    except Stopped:headers['Retry-After']=None
                result=(http_error.code,headers,{})
            except Exception:rejected=True
            finally:
                try:http_error.close()
                except Exception:rejected=True
            if rejected:raise Stopped(RESPONSE_REJECTED)
        return result
