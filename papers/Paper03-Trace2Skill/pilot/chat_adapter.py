"""Chat Completions canary preparation. LIVE_ENABLED stays False in this revision.
No credential lookup, socket call, model listing or endpoint probe is implemented.
Mock transport exercises request/response/accounting only, never live reproduction.
"""
from __future__ import annotations
import datetime as dt
import email.utils
import json
import math
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

BASE_URL='https://models.northern-relay.com/v1'
MODEL='Qwen/Qwen3.5-397B-A17B-FP8'
SECRET_ENV='NR_KEY'  # Only accepted name; no legacy fallback or credential reads in this offline module.
EXPIRES=dt.datetime(2026,11,3,23,38,17,tzinfo=dt.timezone.utc)
LIVE_ENABLED=False
class Stopped(RuntimeError): pass
class LiveDisabled(Stopped): pass

@dataclass(frozen=True)
class Limits:
    # Proposed local ceiling, NOT a reservation against shared account quota.
    tokens:int=100000
    requests:int=40
    rpm:int=60
    tpm:int=500000
    concurrency:int=4
    max_attempts:int=2
    max_retry_wait_seconds:float=30
    request_timeout_seconds:float=30
    wall_seconds:float=900
    safety_margin_seconds:float=60

class Budget:
    """Admission uses trusted input count + maximum output; reservations never refunded.
    This bounds locally admitted tokens only if the provider respects max_tokens and
    the trusted counter includes chat/template/tool overhead. Unknown meter => no call.
    """
    def __init__(self,limits=Limits(),*,clock:Callable=lambda:dt.datetime.now(dt.timezone.utc)):
        if not (1<=limits.concurrency<=4) or not (0<limits.rpm<=60) or not (0<limits.tpm<=500000):
            raise ValueError('canary concurrency/rate policy violated')
        if not (0<limits.tokens<=100000 and 0<limits.requests<=40 and 1<=limits.max_attempts<=2):
            raise ValueError('canary hard budget policy violated')
        self.limits=limits;self.clock=clock;self.start=clock();self.tokens=0;self.requests=0
        self.events=[];self.active=0;self.halted=False;self.lock=threading.Lock()
    def check(self):
        now=self.clock()
        if now.tzinfo is None:raise Stopped('UTC-aware clock required')
        if self.halted:raise Stopped('run halted')
        if now+dt.timedelta(seconds=self.limits.safety_margin_seconds+self.limits.request_timeout_seconds)>=EXPIRES:
            raise Stopped('expired or insufficient pre-expiry request margin')
        if (now-self.start).total_seconds()>=self.limits.wall_seconds:raise Stopped('wall budget exhausted')
    def begin(self,reservation:int):
        with self.lock:
            self.check()
            if type(reservation) is not int or reservation<=0:raise Stopped('trusted positive token reservation required')
            if self.active>=self.limits.concurrency:raise Stopped('experiment-wide concurrency gate')
            now=self.clock();recent=[x for x in self.events if (now-x[0]).total_seconds()<60]
            if self.requests+1>self.limits.requests or self.tokens+reservation>self.limits.tokens:raise Stopped('total budget exhausted')
            if len(recent)>=self.limits.rpm or sum(x[1] for x in recent)+reservation>self.limits.tpm:raise Stopped('rolling rate budget exhausted; no auto wait')
            self.requests+=1;self.tokens+=reservation;self.events.append((now,reservation));self.active+=1
    def end(self):
        with self.lock:
            if self.active<=0:raise RuntimeError("no active reservation to release")
            self.active-=1

def build_request(messages,*,tools=None,max_tokens=512,temperature=0.2):
    if type(max_tokens) is not int or not 1<=max_tokens<=1024:raise ValueError('max_tokens outside canary ceiling')
    if not messages:raise ValueError('messages required')
    out=[]
    for m in messages:
        if set(m)-{'role','content','tool_calls','tool_call_id','name'}:raise ValueError('unknown message fields')
        if m.get('role') not in {'system','user','assistant','tool'}:raise ValueError('unsupported role; explicit conversion required')
        if m.get('content') is not None and not isinstance(m['content'],str):raise ValueError('text-only canary')
        if m['role']=='tool' and not m.get('tool_call_id'):raise ValueError('tool result needs tool_call_id')
        out.append(dict(m))
    payload=dict(model=MODEL,messages=out,max_tokens=max_tokens,temperature=temperature,stream=False,n=1)
    if tools:
        for tool in tools:
            if tool.get('type')!='function' or not tool.get('function',{}).get('name'):raise ValueError('Chat tool schema required')
        payload['tools']=tools;payload['tool_choice']='auto';payload['parallel_tool_calls']=False
    return dict(url=BASE_URL+'/chat/completions',json=payload)

def parse_response(body,allowed_tools=()):
    # Never return provider reasoning, endpoint details or raw errors to artifact logs.
    choices=body.get('choices')
    if not isinstance(choices,list) or len(choices)!=1:raise Stopped('one choice required')
    c=choices[0];m=c.get('message',{});finish=c.get('finish_reason')
    if finish not in ('stop','tool_calls','length'):raise Stopped('unknown finish reason')
    calls=m.get('tool_calls') or []
    if len(calls)>1:raise Stopped('parallel/multiple tool calls disabled for canary')
    if finish=='tool_calls' and not calls:raise Stopped('missing tool call')
    parsed=[]
    for call in calls:
        f=call.get('function',{});name=f.get('name');args=f.get('arguments')
        if call.get('type')!='function' or name not in allowed_tools:raise Stopped('unavailable tool')
        if not call.get('id') or not isinstance(args,str):raise Stopped('invalid tool call')
        try:value=json.loads(args)
        except (ValueError,TypeError):raise Stopped('malformed tool arguments') from None
        if not isinstance(value,dict):raise Stopped('tool arguments must be object')
        parsed.append(dict(id=call['id'],name=name,arguments=value))
    usage=body.get('usage',{})
    for k in ('prompt_tokens','completion_tokens','total_tokens'):
        if type(usage.get(k)) is not int or usage[k]<0:raise Stopped('missing/invalid usage; reservation remains charged')
    if usage['total_tokens']!=usage['prompt_tokens']+usage['completion_tokens']:raise Stopped('inconsistent usage')
    return dict(content=m.get('content') or '',tool_calls=parsed,finish_reason=finish,usage={k:usage[k] for k in ('prompt_tokens','completion_tokens','total_tokens')})

def retry_after(value,now):
    try:seconds=float(value)
    except (TypeError,ValueError):
        try:seconds=(email.utils.parsedate_to_datetime(value)-now).total_seconds()
        except (TypeError,ValueError,OverflowError):raise Stopped('invalid/missing Retry-After') from None
    if not math.isfinite(seconds) or seconds<0:raise Stopped('invalid Retry-After')
    return seconds

class OfflineClient:
    """Injected mocks only. send_live fails BEFORE any credential access/network."""
    def __init__(self,transport,budget:Budget,*,counter=None,sleep=lambda _:None):
        self.transport=transport;self.budget=budget;self.counter=counter;self.sleep=sleep;self.audit=[]
        if getattr(transport,'mode',None)!='offline_mock':raise LiveDisabled('only explicit offline mock transport is accepted')
    def send_live(self,*args,**kwargs):raise LiveDisabled('live disabled; parent budget approval + secure secret provisioning + reviewed network transport required')
    def call(self,request,*,purpose,arm,rollout,allowed_tools=()):
        if purpose not in {'generation','repair','reflection','mutation','compression'}:raise ValueError('unknown purpose')
        if arm not in {'fixed','evolution','interface_test'}:raise ValueError('unknown arm')
        if request.get('url')!=BASE_URL+'/chat/completions' or request['json'].get('model')!=MODEL:raise Stopped('endpoint/model mismatch')
        if self.counter is None:raise Stopped('trusted token counter unavailable; cannot admit')
        predicted=self.counter(request['json'])
        if type(predicted) is not int or predicted<0:raise Stopped('trusted input token count required')
        reserved=predicted+request['json']['max_tokens']
        for attempt in range(1,self.budget.limits.max_attempts+1):
            self.budget.begin(reserved);released=False;start=time.monotonic();status=None
            event=dict(mode='offline_mock',purpose=purpose,arm=arm,rollout=rollout,attempt=attempt,reserved_tokens=reserved,started_utc=self.budget.clock().isoformat())
            try:
                status,headers,body=self.transport(request,timeout=self.budget.limits.request_timeout_seconds)
                event['http_status']=status
                if status in (401,403):self.budget.halted=True;raise Stopped('authentication/authorization failure; run halted')
                if status==429:
                    wait=retry_after(headers.get('Retry-After'),self.budget.clock());event['retry_after_seconds']=wait
                    if attempt>=self.budget.limits.max_attempts:raise Stopped('retry ceiling reached')
                    if wait>self.budget.limits.max_retry_wait_seconds:raise Stopped('Retry-After exceeds wait ceiling; stopped without early retry')
                    self.budget.check()
                    if self.budget.clock()+dt.timedelta(seconds=wait+self.budget.limits.request_timeout_seconds+self.budget.limits.safety_margin_seconds)>=EXPIRES:raise Stopped('retry would cross expiry margin')
                    event['outcome']='retry_scheduled';self.budget.end();released=True;self.sleep(wait);continue
                if status!=200:raise Stopped('non-success response; no implicit retries')
                try:result=parse_response(body,allowed_tools)
                except Stopped:
                    self.budget.halted=True;raise
                event['usage']=result['usage'];event['finish_reason']=result['finish_reason']
                if result['usage']['total_tokens']>reserved:
                    self.budget.halted=True;raise Stopped('usage exceeded reservation; run halted; budget assumption invalid')
                if result['finish_reason']=='length':raise Stopped('output truncated; no automatic repair/retry')
                event['outcome']='success';return result
            except Stopped:
                event['outcome']='stopped';raise
            except Exception:
                # Timeout/transport uncertainty may already have incurred cost. Never retry blindly.
                self.budget.halted=True;event['outcome']='uncertain_transport_stop';raise Stopped('transport failure; charged reservation retained; stopped') from None
            finally:
                if not released:self.budget.end()
                event['elapsed_seconds']=round(time.monotonic()-start,6)
                self.audit.append(event)
        raise Stopped('attempt ceiling')

# No os.environ access. Future model-client process receives NR_KEY only after
# secure provisioning and authorization. Tool worker gets this positive env list.
def worker_environment(workdir:Path):
    return {'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(workdir),'TMPDIR':str(workdir),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}

class ExperimentController:
    """One broker/controller per experiment; all roles/arms share one budget.
    Not a distributed limiter: do not start independent controller processes.
    No production transport exists, and creating a controller never reads a secret.
    """
    def __init__(self,limits=Limits(),*,clock=lambda:dt.datetime.now(dt.timezone.utc)):
        self.budget=Budget(limits,clock=clock)
    def offline_client(self,transport,*,counter=None,sleep=lambda _:None):
        return OfflineClient(transport,self.budget,counter=counter,sleep=sleep)
