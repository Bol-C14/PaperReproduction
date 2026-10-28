"""Execute only the centrally allocated frozen PWM pilot. Raw artifacts remain private."""
import argparse, hashlib, importlib.util, json, os, pathlib, re, subprocess, sys
from decimal import Decimal

def sha(b): return hashlib.sha256(b).hexdigest()
def save(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--shared',required=True);ap.add_argument('--yosys',required=True);ap.add_argument('--out',required=True);ap.add_argument('--live',action='store_true');a=ap.parse_args()
    assert a.live, 'Explicit allocated execution required'
    here=pathlib.Path(__file__).resolve().parent; root=here.parent; plan=json.loads((here/'plan.json').read_text()); freeze=json.loads((here/'freeze.json').read_text())
    assert all(sha((here/n).read_bytes())==h for n,h in freeze['sha256'].items())
    assert sha((here/'plan.json').read_bytes())=='e338adb1593b3877acc9f244b59376b78054ba84c185fbc25804fc5c22ad12d0'
    sys.path.insert(0,a.shared)
    from openrouter_shared import Client,load_config,conservative_chat_quote,batch_status
    batch='vt-pwm-v1-1b74d4f-20261028'; before=batch_status(batch)
    assert before['attempts']==0 and before['pending']==0 and before['remaining_requests']==3
    assert Decimal(before['remaining_usd'])>=Decimal('0.96')
    out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);save(out/'batch_before.json',before)
    data=(root/'continuation/sources/hf_benchmark.jsonl').read_bytes();assert sha(data)=='7090ba304cb5bc07c797ffc94b01ae6006324baa1ea472d472ce0338d81584ca'
    row=json.loads(data.splitlines()[1]);assert sha(row['question'].encode())==plan['question_sha256'] and sha(row['ground_truth'].encode())==plan['gold_sha256']
    base=[{'role':'system','content':plan['system']},{'role':'user','content':plan['initial_user_template'].format(exact_released_question=row['question'])}]
    spec=importlib.util.spec_from_file_location('checks',root/'continuation/run_checks.py');checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
    client=Client(load_config()); stages=[];state={'batch_id':batch,'model':plan['model'],'stages':stages,'status':'started'};save(out/'summary.json',state)
    def stage(name,messages):
        quote=conservative_chat_quote(messages,2048,plan['options']);assert Decimal(quote['reserved_cost_usd'])<=Decimal('0.32')
        w=out/name;w.mkdir();save(w/'messages.json',messages);save(w/'quote.json',quote)
        save(w/'call_started.json',{'stage':name,'message_sha256':sha(json.dumps(messages,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())})
        try:
            response=client.chat(messages,project='verithoughts',run_id='p07-gen-feedback-v1-'+name,max_tokens=2048,max_cost_usd='0.32',authorize_live=True,request_options=plan['options'],batch_id=batch)
        except Exception as exc:
            save(w/'failure.json',{'exception_type':type(exc).__name__,'action':'stop_no_retry_reconcile'});raise
        save(w/'response_private.json',response)
        usage=response.get('usage',{});assert usage.get('cost') is not None, 'Unknown cost: stop'
        assert Decimal(str(usage['cost']))<=Decimal('0.32')
        msg=response['choices'][0]['message'];text=msg.get('content');assert isinstance(text,str),'Nontext output: stop'
        (w/'response.txt').write_text(text)
        (w/'responses.jsonl').write_text(json.dumps({'ground_truth':row['ground_truth'],'full_response':text})+'\n')
        (w/'benchmark.jsonl').write_text(json.dumps({'ground_truth':row['ground_truth'],'verified':True})+'\n')
        (w/'yosys.env').write_text('export PATH='+str(pathlib.Path(a.yosys).resolve().parent)+':$PATH\n')
        command=[sys.executable,str(root/'continuation/original_entrypoint.py'),str(root/'pilot/upstream/evaluation_script.py'),'--results_path','responses.jsonl','--samples_per_question','1','--benchmark_path','benchmark.jsonl','--yosys_location','yosys.env','--reason_mode']
        result=checks.run(command,w,'entrypoint',170);assert result['returncode']==0,'Checker infrastructure failure: stop'
        evaluation=json.loads((w/'responses_evaluation.jsonl').read_text());candidate=(w/'responses/verilog_gen.v').read_text()
        codes=evaluation['stdout_list'];assert codes and all(c in [0,1] for c in codes),'Unknown checker outcome: stop'
        status=batch_status(batch);assert status['pending']==0
        item={'stage':name,'message_sha256':sha((w/'messages.json').read_bytes()),'response_text_sha256':sha(text.encode()),'candidate_sha256':sha(candidate.encode()),'finish_reason':response['choices'][0].get('finish_reason'),'usage':{k:usage[k] for k in ['prompt_tokens','completion_tokens','total_tokens','cost'] if k in usage},'original_success':evaluation['success'],'guarded_success':bool(candidate.strip()) and bool(codes) and evaluation['success'],'yosys_returncodes':codes,'checker_wall_seconds':result['wall_seconds'],'checker_cpu_seconds':result['cpu_seconds'],'batch_status':status}
        stages.append(item);save(out/'summary.json',state)
        return item,text,w
    first,text,w=stage('initial',base)
    if first['original_success']:
        state['status']='initial_bounded_pass_stop_no_feedback_opportunity'
    else:
        stderr=(w/'yosys_0.stderr.log').read_text();stdout=(w/'yosys_0.stdout.log').read_text()
        if not (w/'responses/verilog_gen.v').read_text().strip():category='empty_candidate'
        elif 'syntax error' in stderr:category='syntax_error'
        elif "Can't find gate module" in stderr:category='missing_module'
        elif 'SAT proof finished - model found: FAIL!' in stdout:category='bounded_counterexample'
        else:raise RuntimeError('Unknown failure category: stop')
        # Use only actual tool outcome lines; never send source or raw trace/path content.
        diagnostic='\n'.join(line for line in (stdout+'\n'+stderr).splitlines() if 'SAT proof finished' in line or 'ERROR:' in line)
        diagnostic=re.sub(r'(?:/[^\s:]+)+','<path>',diagnostic)
        diagnostic=diagnostic.replace('responses\\verilog_gen.v','<candidate>').replace('responses/verilog_gen.v','<candidate>')
        if len(diagnostic)>4096:diagnostic=diagnostic[:2048]+'\n[diagnostic excerpt]\n'+diagnostic[-2048:]
        nofeedback=base+[{'role':'user','content':plan['retry_no_feedback']}]
        feedback=base+[{'role':'assistant','content':text},{'role':'user','content':plan['retry_feedback_template'].format(category=category,diagnostic=diagnostic)}]
        for msgs in [nofeedback,feedback]:assert Decimal(conservative_chat_quote(msgs,2048,plan['options'])['reserved_cost_usd'])<=Decimal('0.32')
        save(out/'followups_frozen.json',{'no_feedback':nofeedback,'feedback':feedback,'category':category,'diagnostic_policy':'actual outcome/error lines only; excludes full raw traces and source'})
        stage('no_feedback',nofeedback);stage('feedback',feedback);state['status']='matched_second_attempts_completed'
    state['actual_cost_usd']=str(sum((Decimal(str(x['usage']['cost'])) for x in stages),Decimal(0)))
    state['batch_after']=batch_status(batch);save(out/'summary.json',state)
    print(json.dumps({'status':state['status'],'calls':len(stages),'actual_cost_usd':state['actual_cost_usd']}))

if __name__=='__main__':main()
