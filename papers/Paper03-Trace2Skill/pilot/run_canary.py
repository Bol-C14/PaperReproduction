#!/usr/bin/env python3
"""Executable fixture plumbing canary: Chat -> skill/RTL -> real isolated verifier.
Default plan only. --offline-integration mocks Chat ONLY, never the verifier.
--live needs a single-use explicit parent approval; this revision was never run live.
"""
import argparse,concurrent.futures,datetime as dt,hashlib,json,os,re,threading
from dataclasses import replace
from pathlib import Path
from chat_adapter import Limits,MODEL,BASE_URL,EXPIRES,build_request,Stopped,LiveDisabled
from runtime_accounting import Ledger,AccountedChat
from isolated_verifier import RealAdderVerifier,candidate_source
from live_transport import LiveChatTransport,validate_approval

P=Path(__file__).resolve().parents[1]
SEED='Preserve the adder module ports. Implement unsigned addition with a carry bit. Use combinational RTL only. No directives or simulation-control tasks. Return only the requested artifact.'
SPEC='Repair module adder: inputs logic [3:0] A,B; output logic [4:0] X must equal unsigned A+B for all pairs. Return a single complete SystemVerilog module. No initial/final blocks, directives, system tasks, testbench, or prose.'
GOOD='module adder #(parameter integer DATA_WIDTH=4)(input logic [DATA_WIDTH-1:0] A,B, output logic [DATA_WIDTH:0] X); assign X={1\'b0,A}+{1\'b0,B}; endmodule'
BAD=GOOD.replace("{1'b0,A}+{1'b0,B}",'A|B')

def clean_skill(text):
    if not isinstance(text,str) or not 10<=len(text.strip())<=1800:raise ValueError('skill length/format rejected')
    if re.search(r'NR_KEY|Authorization|Bearer\s|sk-[A-Za-z0-9_-]{20,}',text,re.I):raise ValueError('sensitive output rejected')
    return text.strip()

def sha(text):return hashlib.sha256(text.encode()).hexdigest()

class MockChat:
    mode='offline_mock_chat'
    def __init__(self):self.lock=threading.Lock();self.generations=0
    def __call__(self,request,timeout):
        role=request['json']['messages'][0]['content']
        with self.lock:
            if 'ROLE:generation' in role or 'ROLE:repair' in role:
                self.generations+=1;content=BAD if self.generations in (1,5) else GOOD
            elif 'ROLE:reflection' in role:content='Retain the carry bit, preserve ports, and verify addition rather than bitwise OR.'
            else:content=SEED+' Preserve both input operands and the full carry.'
        return 200,{}, {'choices':[{'message':{'role':'assistant','content':content},'finish_reason':'stop'}],'usage':{'prompt_tokens':80,'completion_tokens':40,'total_tokens':120}}

class Canary:
    def __init__(self,chat,verifier,output,*,repairs=0):
        self.chat=chat;self.verifier=verifier;self.output=Path(output);self.repairs=repairs;self.events=[];self.lock=threading.Lock();self.skills={};self.lesson={};self.champions={}
        self.output.mkdir(parents=True,exist_ok=False);self.chat.on_change=self.flush
    def flush(self):
        with self.lock:
            report={'scope':'public adder infrastructure fixture; NOT CVDP; no method-advantage inference','chat_mode':self.chat.transport.mode,'real_model_requests':getattr(self.chat.transport,'network_attempts',0),'admitted_chat_attempts':len(self.chat.ledger.rows),'mock_chat_attempts':len(self.chat.ledger.rows) if self.chat.transport.mode!='live_chat_completions' else 0,'real_verifier_executions':len(self.verifier.rows),'events':list(self.events),'validated_skill_state':{a:[{'text':s,'sha256':sha(s)} for s in v] for a,v in self.skills.items()},'validated_lessons':dict(self.lesson),'verifiers':list(self.verifier.rows),'budget':self.chat.ledger.snapshot(),'matching':'same 50k reservation cap per arm, same nominal role slots; fixed shadow-updates discarded; realized tokens/retries may differ'}
            tmp=self.output/'report.tmp';tmp.write_text(json.dumps(report,indent=2)+'\n');tmp.replace(self.output/'report.json')
    def call(self,purpose,arm,rid,prompt):
        request=build_request([{'role':'system','content':'ROLE:'+purpose+'\n'+('Return only procedural skill text.' if purpose in ('reflection','mutation') else SPEC)},{'role':'user','content':prompt}],max_tokens=1024,temperature=.2)
        # Official Qwen supports this option; provider acceptance remains an actual live check.
        request['json']['chat_template_kwargs']={'enable_thinking':False}
        try:
            text=self.chat.call(request,arm=arm,purpose=purpose,rollout=rid)
            if re.search(r'NR_KEY|Authorization|Bearer\s|sk-[A-Za-z0-9_-]{20,}',text,re.I):raise ValueError('sensitive response rejected before artifact recording')
            with self.lock:self.events.append({'type':'response_artifact','purpose':purpose,'arm':arm,'rollout':rid,'response_sha256':sha(text)})
            return text
        finally:self.flush()
    def rollout(self,arm,g,i,skill):
        rid=f'{arm}.g{g}.i{i}.r0';event={'rollout':rid,'arm':arm,'generation':g,'individual':i,'skill_sha256':sha(skill),'status':'NOT_RUN','pass':False}
        try:
            source=self.call('generation',arm,rid,'SKILL:\n'+skill+'\nTASK:\n'+SPEC+'\nVisible buggy statement: assign X = A | B;')
            for repair in range(self.repairs+1):
                try:
                    source=candidate_source(source);result=self.verifier(source,rollout=rid+f'.attempt{repair}');event.update(status=result['status'],pass_=result['pass']);event['pass']=result['pass'];event['source_sha256']=sha(source)
                    # Allowed artifact only; no full prompts, provider reasoning or error body.
                    (self.output/(rid+f'.attempt{repair}.sv')).write_text(source)
                except ValueError:event['status']='rejected_source';event['pass']=False
                if event['pass'] or repair==self.repairs:break
                source=self.call('repair',arm,rid,'SKILL:\n'+skill+'\nTASK:\n'+SPEC+'\nPrior attempt:\n'+source[:2000]+'\nVerifier category: '+event['status'])
        except (Stopped,ValueError):event['status']='stopped_or_rejected';event['pass']=False
        except Exception:
            self.chat.ledger.halted=True;event['status']='infrastructure_error';event['pass']=False
        finally:
            event.pop('pass_',None)
            with self.lock:self.events.append(event)
            self.flush()
        return event
    def run(self):
        try:
            # Same role/call structure for both arms. Fixed generates shadow text but never adopts it.
            for arm in ['fixed','evolution']:
                text=clean_skill(self.call('mutation',arm,'initial_mutation',SEED+'\nImprove this procedural skill conservatively.'))
                self.skills[arm]=[SEED,SEED if arm=='fixed' else text]
            for generation in [1,2]:
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    futures={(arm,i):pool.submit(self.rollout,arm,generation,i,self.skills[arm][i]) for arm in ['fixed','evolution'] for i in [0,1]}
                    batch={key:f.result() for key,f in futures.items()}
                for arm in ['fixed','evolution']:
                    winner=max([0,1],key=lambda i:(batch[arm,i]['pass'],-i));parent=self.skills[arm][winner];self.champions[arm]=parent
                    with self.lock:self.events.append({'type':'evaluated_survivor','arm':arm,'generation':generation,'individual':winner,'skill_sha256':sha(parent),'rule':'final real verifier pass; deterministic lowest-index tie-break'})
                    if generation==1:
                        evidence=[{k:batch[arm,i][k] for k in ['individual','status','pass','skill_sha256']} for i in [0,1]]
                        lesson=clean_skill(self.call('reflection',arm,'g1_reflection','Summarize both successful and failed attempts into procedural lessons.\n'+json.dumps(evidence)))
                        child=clean_skill(self.call('mutation',arm,'g2_child','PARENT:\n'+parent+'\nLESSONS:\n'+lesson+'\nRetain durable rules. Return a compact replacement skill.'))
                        self.lesson[arm]=lesson
                        # Fresh generation2 calls re-evaluate parent; no cached fitness.
                        self.skills[arm]=[SEED,SEED] if arm=='fixed' else [parent,child]
                self.flush()
        except (Stopped,ValueError):
            with self.lock:self.events.append({'type':'run_stopped','reason':'budget, authorization, protocol or bounded content validation; inspect allowlisted ledger'})
        finally:self.flush()
        return json.loads((self.output/'report.json').read_text())

def main():
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group();group.add_argument('--offline-integration',action='store_true');group.add_argument('--live',action='store_true');parser.add_argument('--approval',type=Path);parser.add_argument('--out',type=Path);parser.add_argument('--image-id');parser.add_argument('--repair-attempts',type=int,choices=[0,1],default=0);args=parser.parse_args()
    if not args.live and not args.offline_integration:
        print(json.dumps({'status':'PLAN_ONLY','live_requests':0,'task':'public adder fixture only','nominal_chat_calls':14,'real_verifier_calls':8,'per_arm_token_ceiling':50000,'total_ceiling':100000,'shared_concurrency':4,'counter':'conservative estimate, NOT proven provider hard token bound','command_after_parent_activation':'python3 pilot/run_canary.py --live --approval /workspace/private/nr-canary-approval.json --out runs/nr-fixture-canary'},indent=2));return 0
    if args.out is None:parser.error('--out required; never overwrite a run')
    if args.live:
        try:
            validate_approval(args.approval)
            marker=Path(str(args.approval)+'.started');fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
            transport=LiveChatTransport(args.approval)
        except (OSError,ValueError,KeyError,LiveDisabled):print(json.dumps({'status':'BLOCKED_BEFORE_SECRET_OR_NETWORK','model_requests':0}));return 2
    else:transport=MockChat()
    verifier=RealAdderVerifier(args.image_id) if args.image_id else RealAdderVerifier()
    ledger=Ledger();chat=AccountedChat(transport,ledger);canary=Canary(chat,verifier,args.out,repairs=args.repair_attempts);report=canary.run()
    print(json.dumps({'scope':report['scope'],'chat_mode':report['chat_mode'],'model_requests':report['real_model_requests'],'mock_chat_attempts':report['mock_chat_attempts'],'real_verifier_executions':report['real_verifier_executions'],'report':str(args.out/'report.json')},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
