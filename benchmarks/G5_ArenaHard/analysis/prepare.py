"""Bounded, pinned public-data acquisition; never executes model text."""
import json, hashlib, pathlib, urllib.request, sys, time
ROOT=pathlib.Path(sys.argv[1]); ROOT.mkdir(parents=True,exist_ok=True)
REV='15f3746e21432264ce9b453999bde4f3c946d2e6'
MODELS=['gpt-4-turbo-2024-04-09','claude-3-opus-20240229','claude-3-sonnet-20240229','gpt-4-0314','gpt-4-0613','mistral-large-2402','qwen1.5-72b-chat','mistral-medium','claude-2.0','gpt-3.5-turbo-0613','claude-2.1','gemini-pro','mixtral-8x7b-instruct-v0.1','gpt-3.5-turbo-0314','yi-34b-chat','tulu-2-dpo-70b','dbrx-instruct-preview','vicuna-33b','starling-lm-7b-alpha','llama-2-70b-chat']
JUDGES=['gpt-4-1106-preview','gemini-1.5-pro-api-0514']
base='data/arena-hard-v0.1/'
paths=[base+'question.jsonl']+[base+'model_answer/'+m+'.jsonl' for m in MODELS]+[base+'model_judgment/'+j+'/'+m+'.jsonl' for j in JUDGES for m in MODELS if m!='gpt-4-0314']+['README.md','.gitattributes']
plan={'dataset_revision':REV,'models':MODELS,'judges':JUDGES,'baseline':'gpt-4-0314','paths':paths,'budget':{'download_bytes':2000000000,'cpu_threads':4,'paid_calls':0,'preparation_hours':2},'sample_rule':'question_id sorted lexicographically; first 50 for initial four-model sample; all 500 for main','pilot_models':MODELS[:3]+['llama-2-70b-chat'],'missing_policy':'retain every requested file and missing question; common complete valid two-game question intersection across selected models/judges for matched sensitivity, no imputation; report full primary separately','invalid_scores':'exclude invalid game from upstream scoring; exclude question from matched complete sensitivity; enumerate','bootstrap':'100 rounds upstream battle-row bootstrap seed42; 1000 paired question-cluster rounds seed20261028 as sensitivity','human_checks':'summary-only if JSON present; no pickle execution; full raw human alignment not_run'}
(ROOT/'selection-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]; used=0
for path in paths:
 dest=ROOT/path; dest.parent.mkdir(parents=True,exist_ok=True); url=f'https://huggingface.co/datasets/lmarena-ai/arena-hard-auto/resolve/{REV}/{path}'
 item={'path':path,'url':url,'status':'not_run'}
 try:
  if not dest.exists():
   with urllib.request.urlopen(url,timeout=90) as r:
    data=r.read(min(20000000,2000000000-used)+1)
   if len(data)>20000000 or used+len(data)>2000000000: raise RuntimeError('download cap')
   dest.write_bytes(data)
  data=dest.read_bytes(); used+=len(data)
  item.update(status='downloaded',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 except Exception as e: item.update(status='infrastructure_failure',error=str(e))
 rows.append(item); (ROOT/'acquisition.json').write_text(json.dumps(rows,indent=2)+'\n'); print(json.dumps(item),flush=True)
print(json.dumps({'total_file_bytes':used,'failed':sum(x['status']!='downloaded' for x in rows)}),flush=True)
