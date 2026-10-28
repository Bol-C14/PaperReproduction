"""Shared admission reservations + usage settlement for the executable canary."""
import datetime as dt,hashlib,json,threading,time
from chat_adapter import EXPIRES,Limits,Stopped,retry_after

def conservative_count(payload):
    # Official tokenizer download was HTTP403. Not a tokenizer or proven bound.
    # Serialize all fields, charge one token per UTF8 byte + 2048 template margin.
    return len(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode())+2048

def usage_total(body):
    if not isinstance(body,dict):return None
    u=body.get('usage',{})
    if all(type(u.get(k)) is int and u[k]>=0 for k in ['prompt_tokens','completion_tokens','total_tokens']) and u['total_tokens']==u['prompt_tokens']+u['completion_tokens']:
        return u['total_tokens']
    return None

class Ledger:
    def __init__(self,limits=Limits(),*,clock=lambda:dt.datetime.now(dt.timezone.utc),slot_reservation=6144):
        if not (0<limits.tokens<=100000 and 0<limits.requests<=40 and 0<limits.concurrency<=4 and 0<limits.rpm<=60 and 0<limits.tpm<=500000):raise ValueError('experiment ceilings')
        self.limits=limits;self.clock=clock;self.start=clock();self.slot=slot_reservation;self.lock=threading.Lock();self.active={};self.rows=[];self.halted=False;self.reserved=0;self.charged=0;self.arm_reserved={'fixed':0,'evolution':0}
    def check(self):
        now=self.clock()
        if now.tzinfo is None or self.halted:raise Stopped('run stopped')
        if now+dt.timedelta(seconds=90)>=EXPIRES:raise Stopped('expiry safety margin')
        if (now-self.start).total_seconds()>=self.limits.wall_seconds:raise Stopped('wall budget')
    def begin(self,payload,arm,purpose,rollout,attempt):
        with self.lock:
            self.check();estimate=conservative_count(payload)+payload['max_tokens'];reserve=max(self.slot,estimate)
            if arm not in self.arm_reserved:raise Stopped('unknown arm')
            recent=[r for r in self.rows if (self.clock()-dt.datetime.fromisoformat(r['started_utc'])).total_seconds()<60]
            if len(self.active)>=self.limits.concurrency:raise Stopped('global concurrency ceiling')
            if len(self.rows)>=self.limits.requests or self.reserved+reserve>self.limits.tokens or self.arm_reserved[arm]+reserve>self.limits.tokens//2:raise Stopped('matched per-arm or global reservation ceiling')
            if len(recent)>=self.limits.rpm or sum(r['reserved_tokens'] for r in recent)+reserve>self.limits.tpm:raise Stopped('rolling rate ceiling')
            i=len(self.rows);row={'attempt_id':i,'payload_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),'arm':arm,'purpose':purpose,'rollout':rollout,'attempt':attempt,'started_utc':self.clock().isoformat(),'reserved_tokens':reserve,'input_estimate_tokens':estimate-payload['max_tokens'],'counter':'utf8-byte-plus2048 ESTIMATE; not a proven provider token bound','charged_tokens':reserve,'usage_known':False,'status':'in_flight','mode':None}
            self.rows.append(row);self.active[i]=time.monotonic();self.reserved+=reserve;self.charged+=reserve;self.arm_reserved[arm]+=reserve;return i
    def finish(self,i,*,status,body=None,http_status=None,mode=None):
        with self.lock:
            row=self.rows[i];actual=usage_total(body);start=self.active.pop(i)
            if actual is not None:
                self.charged+=actual-row['charged_tokens'];row['charged_tokens']=actual;row['usage_known']=True;row['usage']={k:body['usage'][k] for k in ['prompt_tokens','completion_tokens','total_tokens']}
                if actual>row['reserved_tokens']:self.halted=True;row['reservation_underestimated']=True
            row.update(status=status,http_status=http_status,mode=mode,elapsed_seconds=round(time.monotonic()-start,6))
    def snapshot(self):
        with self.lock:return {'requests':len(self.rows),'cumulative_admission_reservations':self.reserved,'settled_known_plus_conservative_unknown_tokens':self.charged,'per_arm_reservations':dict(self.arm_reserved),'active':len(self.active),'halted':self.halted,'provider_token_cap_proven':False,'rows':[dict(r) for r in self.rows]}

class AccountedChat:
    def __init__(self,transport,ledger,*,sleep=time.sleep):self.transport=transport;self.ledger=ledger;self.sleep=sleep;self.on_change=lambda:None
    def call(self,request,*,arm,purpose,rollout):
        from chat_adapter import parse_response,BASE_URL,MODEL
        if request['url']!=BASE_URL+'/chat/completions' or request['json']['model']!=MODEL:raise Stopped('wrong remote route/model')
        for attempt in range(1,self.ledger.limits.max_attempts+1):
            i=self.ledger.begin(request['json'],arm,purpose,rollout,attempt);finished=False;status=None;body=None
            try:
                self.on_change()  # persist admission before any possible network request
                status,headers,body=self.transport(request,timeout=self.ledger.limits.request_timeout_seconds)
                if status in [401,403]:self.ledger.halted=True;raise Stopped('authentication/authorization failure; entire run stopped')
                if status==429:
                    delay=retry_after(headers.get('Retry-After'),self.ledger.clock())
                    if attempt>=self.ledger.limits.max_attempts or delay>self.ledger.limits.max_retry_wait_seconds:raise Stopped('429 retry/wait bound')
                    if self.ledger.clock()+dt.timedelta(seconds=delay+90)>=EXPIRES:raise Stopped('429 expiry bound')
                    self.ledger.finish(i,status='429_retry',body=body,http_status=status,mode=self.transport.mode);finished=True;self.sleep(delay);continue
                if status!=200:
                    self.ledger.halted=True;raise Stopped('HTTP failure; stop new calls, no implicit retry')
                choices=body.get('choices',[]) if isinstance(body,dict) else []
                if len(choices)!=1 or choices[0].get('finish_reason')!='stop':raise Stopped('nonfinal/truncated output; explicit repair only')
                message=choices[0].get('message',{})
                if message.get('tool_calls') or not isinstance(message.get('content'),str):raise Stopped('text-only final completion required')
                parsed={'content':message['content']}
                self.ledger.finish(i,status='success',body=body,http_status=status,mode=self.transport.mode);finished=True
                if self.ledger.halted:raise Stopped('provider usage exceeded estimated reservation; halted')
                return parsed['content']
            except Stopped:
                if not finished:self.ledger.finish(i,status='stopped',body=locals().get('body'),http_status=locals().get('status'),mode=self.transport.mode);finished=True
                raise
            except Exception:
                self.ledger.halted=True
                if not finished:self.ledger.finish(i,status='uncertain_transport_stop',mode=self.transport.mode);finished=True
                raise Stopped('transport outcome uncertain; full reservation charged; no retry') from None
        raise Stopped('retry limit')
