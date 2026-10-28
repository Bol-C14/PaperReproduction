"""Prepare by default. Live mode requires a separate explicit parent release.

No policy mutation, credential copying, model fallback, retry, or concurrency.
Only the shared public Client.chat interface performs paid requests.
"""
import argparse, fcntl, hashlib, importlib.util, json, os, re
from pathlib import Path
BATCH='cf-rtl19-v1-20261028'
PROJECT='circuitfusion'
MODEL='google/gemini-2.5-flash'
SYSTEM=('Summarize the combinational next_state function of this HDL register cone '
        'in 2-4 plain sentences. State input dependencies, selection conditions, '
        'widths, signedness and arithmetic or logical behavior where clear. Do not '
        'invent reset, clocks, physical properties or signal meanings. Avoid wire '
        'names, source IDs, implementation statistics and graph structure. Return '
        'JSON with string fields summary and uncertainty.')

def digest(b):return hashlib.sha256(b).hexdigest()
def messages_for(code):
    # Generated tool comments contain build paths: remove before external transport.
    code=re.sub(r'/\*.*?\*/|//[^\n]*','',code,flags=re.S).strip()
    if re.search(r'/Users/|/home/|/workspace/',code):raise ValueError('path in HDL payload')
    return [{'role':'system','content':SYSTEM},{'role':'user','content':code}]
def write_json(path,value):
    # Caller directory must be private; no response ID or credential is persisted.
    path.write_text(json.dumps(value,indent=2)+'\n');os.chmod(path,0o600)

def main():
    p=argparse.ArgumentParser();p.add_argument('--shared-client',type=Path,required=True)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--released-batch',choices=[BATCH],default=None,
                   help='Use ONLY after explicit parent release; omission is preparation only')
    a=p.parse_args();spec=importlib.util.spec_from_file_location('shared_openrouter',a.shared_client)
    shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
    a.output.mkdir(parents=True,exist_ok=True,mode=0o700)
    if a.output.is_symlink() or a.output.stat().st_mode&0o077:raise ValueError('output directory must be private mode700')
    manifest=json.loads((a.root/'manifest.json').read_text());assert len(manifest)==19
    old_quotes={r['sample_id']:r for r in json.loads((a.root/'api_quote_plan.json').read_text())['quotes']}
    plan=[];messages={}
    for r in manifest:
        sid=r['sample_id'];source=(a.root/'data'/sid/'cone.v').read_bytes()
        if digest(source)!=old_quotes[sid]['source_sha256']:raise ValueError('frozen source changed')
        msg=messages_for(source.decode());msg[1]['content']='ISC notice:\n'+(a.root/'assets/YOSYS_COPYING').read_text()+'\nHDL:\n'+msg[1]['content'];messages[sid]=msg
        quote=shared.conservative_chat_quote(msg,512,{'temperature':0,'reasoning':{'enabled':False}},model=MODEL)
        plan.append({'sample_id':sid,'source_sha256':digest(source),
                     'messages_sha256':digest(json.dumps(msg,sort_keys=True).encode()),'quote':quote})
    write_json(a.output/'request_plan.json',{'batch_id':BATCH,'model':MODEL,'requests':plan,
               'generation_requests':19,'max_total_attempts':21,'corrections_reserved':2,
               'serial':True,'max_output_tokens':512,'live_requested':a.released_batch is not None})
    if a.released_batch is None:
        print(json.dumps({'mode':'prepared','requests':19,'live_calls':0,'batch_id':BATCH}));return
    # This branch must not be used until a human-authorized parent release arrives.
    with (a.output/'runner.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if list(a.output.glob('*.pending')):raise RuntimeError('uncertain prior outcome; reconcile before any call')
        status=shared.batch_status(BATCH)
        if status['project']!=PROJECT or status['pending'] or status['attempts']>21:
            raise RuntimeError('batch not ready')
        client=shared.Client(shared.load_config())
        for row in plan:
            sid=row['sample_id'];dest=a.output/(sid+'.json')
            if dest.exists():
                done=json.loads(dest.read_text())
                if done.get('usage',{}).get('cost') is None or done.get('finish_reason')!='stop':raise ValueError('saved result requires reconciliation')
                if done['messages_sha256']!=row['messages_sha256']:raise ValueError('completed input changed')
                continue
            status=shared.batch_status(BATCH)
            if status['pending'] or status['remaining_requests']<=2 or status['attempts']>=19:
                raise RuntimeError('generation limit or unresolved reservation; stop')
            pending=a.output/(sid+'.pending');pending.touch(exist_ok=False);os.chmod(pending,0o600)
            # Exceptions intentionally leave the pending marker. Never retry an
            # uncertain outcome; ledger reconciliation is a separate explicit step.
            response=client.chat(messages[sid],project=PROJECT,run_id='rtl19-'+sid,
                batch_id=BATCH,max_tokens=512,max_cost_usd='0.32',authorize_live=True,
                request_options={'temperature':0,'reasoning':{'enabled':False},
                                 'response_format':{'type':'json_object'}})
            choice=response['choices'][0];content=choice['message']['content']
            # Persist exact text content first; parsing failure must not lose paid evidence.
            record={'sample_id':sid,'batch_id':BATCH,'source_sha256':row['source_sha256'],
                    'messages_sha256':row['messages_sha256'],'content':content,
                    'usage':{k:v for k,v in (response.get('usage') or {}).items()
                             if k in ['prompt_tokens','completion_tokens','total_tokens','cost']},
                    'finish_reason':choice.get('finish_reason')}
            write_json(dest,record);pending.unlink()
            if record['usage'].get('cost') is None:raise ValueError('unknown cost; stop for reconciliation')
            parsed=json.loads(content)
            if choice.get('finish_reason')!='stop' or not all(isinstance(parsed.get(k),str) for k in ['summary','uncertainty']):
                raise ValueError('incomplete or invalid caption; preserve and stop for review')
            print(json.dumps({'sample_id':sid,'status':'received_unreviewed'}),flush=True)

if __name__=='__main__':main()
