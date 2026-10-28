#!/usr/bin/env python3
import os,time,json,hashlib,sys,shutil,platform
from pathlib import Path
R=Path(os.environ.get('PAPER_REPRO_ROOT','/home/shugu/work/paper-reproduction-april-20261028')); SRC=Path(__file__).resolve().parents[1]/'closed_loop'; OUT=R/'results/crop/live-pilot'
OUT.mkdir(parents=True,exist_ok=True); sys.path.insert(0,str(SRC))
import study,model_contract
from api_adapter import ChatAPI
if not (R/'results/crop/API_AUTHORIZED.json').exists(): raise SystemExit('API endpoint and public-data scope await parent authorization')
api=ChatAPI(allow_network=True)
E=R/'assets/shared/all-minilm-l6-v2'
MODEL=os.environ.get('PAPER_LLM_MODEL','');EREV='1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
def save(p,o): study.dump(OUT/p,o)
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
if (OUT/'budget.json').exists(): raise SystemExit('Pilot refuses overwrite')
save('budget.json',dict(frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),source_commit='a7b6f8dbfcc2b1c2c8a90d9c29c315388a253e7f',seed=23,summary_circuits=7,summary_stages=2,summary_attempts_per_stage=2,max_proposals=3,max_attempts_per_proposal=2,max_new_eda_measurements=4,max_new_prior_measurements=0,max_input_tokens=4096,max_new_tokens=640,decoding='greedy',api_model=MODEL,minilm_revision=EREV,prior_history_sha256=hashlib.sha256((SRC/'history.json').read_bytes()).hexdigest(),objective='LUT4 count * maximum unit LUT depth',limitations=['single-module hierarchy','free-tool and model substitutions','no paper-quality claim']))
save('versions.json',dict(python=platform.python_version(),cpu_affinity=sorted(os.sched_getaffinity(0)),model_backend='authorized OpenAI-compatible API'))
def generate(label,prompt,required=None):
 messages=[{'role':'system','content':'You are a precise RTL synthesis assistant. Output exactly one valid JSON object with no markdown or explanations outside JSON. Use the exact requested keys.'},{'role':'user','content':prompt}]
 record=dict(prompt=prompt,prompt_sha256=sha(prompt))
 try:
  record.update(api.complete(messages,max_tokens=640))
  raw=record['raw_output'];cleaned=raw.strip();fence=chr(96)*3
  if cleaned.startswith(fence):cleaned=cleaned.split('\n',1)[1].rsplit(fence,1)[0].strip()
  obj=json.loads(cleaned)
  if required is not None and set(obj)!=required:raise ValueError('Wrong exact keys')
  record['status']='parsed'
 except Exception as ex:record.update(status='invalid',error=str(ex));obj=None
 save(Path('generations')/(label+'.json'),record);print(label,record['status'],flush=True)
 return obj,record
manifest=json.loads((SRC/'manifest.json').read_text());designs=[d for d in manifest['designs'] if d['role']=='prior' or d['id']=='fir3'];caches={}
for d in designs:
 source=(SRC/d['rtl']).read_text();records=[];module=None
 for attempt in range(2):
  prompt='Summarize this actual unsigned combinational Verilog module as JSON with EXACT keys '+json.dumps(sorted(model_contract.MODULE_FIELDS))+'. Each value a concise string. State widths, arithmetic/truncation, and combinational timing limitations. RTL:\n'+source
  module,rec=generate(d['id']+'_module_'+str(attempt),prompt,model_contract.MODULE_FIELDS);records.append(rec)
  if module is not None: break
 if module is None: raise SystemExit('Module summary budget exhausted')
 circuit=None
 for attempt in range(2):
  prompt='Build a whole-design summary ONLY from the following module summary. There is one top module dut, no child instances. Return JSON with EXACT keys '+json.dumps(sorted(model_contract.DESIGN_FIELDS))+'. Each value a concise string. Do not invent clocks, physical timing or hierarchy.\nMODULE SUMMARY:\n'+json.dumps(module)
  circuit,rec=generate(d['id']+'_design_'+str(attempt),prompt,model_contract.DESIGN_FIELDS);records.append(rec)
  if circuit is not None: break
 if circuit is None: raise SystemExit('Design summary budget exhausted')
 caches[d['id']]=dict(source_sha256=sha(source),modules=[dict(name='dut',summary=module)],design_summary=circuit,summary_model=MODEL,summary_model_revision=records[-1].get('model',MODEL),embedding_model='sentence-transformers/all-MiniLM-L6-v2',embedding_model_revision=EREV,prompt_sha256=study.digest([r['prompt_sha256'] for r in records]),embedding_normalization='L2 unit norm',embedding_truncation='max_seq_length=256; token counts recorded',generation_provenance=dict(live=True,stages=['RTL module summary','design summary from module summary'],attempts=len(records),seed=23,greedy=True))
 save(Path('summaries')/(d['id']+'.json'),caches[d['id']])
from sentence_transformers import SentenceTransformer
encoder=SentenceTransformer(str(E),local_files_only=True,trust_remote_code=False,device='cpu')
for name,cache in caches.items():
 text=json.dumps(cache['design_summary'],sort_keys=True);cache['embedding']=encoder.encode(text,normalize_embeddings=True).tolist();cache['embedding_input_tokens']=len(encoder.tokenizer(text)['input_ids']);cache['embedding_max_seq_length']=encoder.max_seq_length
 model_contract.summary_cache(cache,cache['source_sha256']);save(Path('summaries')/(name+'.json'),cache)
priors=[d['id'] for d in designs if d['role']=='prior'];sims=sorted([(sum(a*b for a,b in zip(caches['fir3']['embedding'],caches[n]['embedding'])),n) for n in priors],key=lambda x:(-x[0],x[1]))
history=json.loads((SRC/'history.json').read_text());selected=sims[0][1];base=next(r['objective'] for r in history[selected] if r['config']=='c0')
guidance=[dict(config=r['config'],objective=r['objective'],normalized_objective=r['objective']/base) for r in history[selected][:3]]
save('retrieval.json',dict(similarities=sims,selected=selected,guidance=guidance,history_sha256=hashlib.sha256((SRC/'history.json').read_bytes()).hexdigest()))
exp=OUT/'experiment';exp.mkdir()
for directory in ['circuits','abc_scripts']: shutil.copytree(SRC/directory,exp/directory)
m=dict(manifest);m['max_measurement_calls']=4;study.dump(exp/'manifest.json',m);study.ROOT=exp;study.YOSYS=R/'tools/crop/yosys/yosys';study.ABC=R/'tools/abc-rl/abc/abc'
st=study.Study();target=st.designs['fir3'];byconfig={c['id']:c for c in m['configs']};archive=[]
row=st.measure(target,byconfig['c0'],'live_model',seed=23,iteration=0)
if row['status']!='ok': raise SystemExit('Baseline EDA failure')
archive.append(dict(config=row['config'],objective=row['objective'],status='ok',invocation=row['invocation']))
save('target_archive.json',archive)
for iteration in range(1,4):
 context=dict(arm='semantic_llm',seed=23,iteration=iteration,legal_configs=m['configs'],retrieved_prior=selected,retrieved_guidance=guidance,target_history=archive,objective=m['score'],prior_db_hash=study.digest(history),target_history_hash=study.digest(archive),design_summary=caches['fir3']['design_summary']);chosen=None
 for attempt in range(2):
  prompt='Choose one legal UNTRIED synthesis configuration to minimize the objective. Use prior guidance and actual target observations; explore if uncertain. Return exactly {"configuration":{"mode": string,"noalumacc": boolean}}. Do not return id. Context:\n'+json.dumps(context)
  response,record=generate('proposal_'+str(iteration)+'_'+str(attempt),prompt)
  try:
   if response is None: raise ValueError('No parsed response')
   chosen=model_contract.proposal(response,context)
  except Exception as ex: save(Path('rejections')/(str(iteration)+'_'+str(attempt)+'.json'),dict(error=str(ex),response=response));continue
  save(Path('contexts')/(str(iteration)+'.json'),dict(request=context,response=response,chosen=chosen));break
 if chosen is None: raise SystemExit('Proposal budget exhausted; no heuristic fallback')
 row=st.measure(target,byconfig[chosen],'live_model',seed=23,iteration=iteration,retrieved=selected)
 if row['status']!='ok': raise SystemExit('Candidate EDA failed')
 archive.append(dict(config=row['config'],objective=row['objective'],status='ok',invocation=row['invocation']));save('target_archive.json',archive)
save('outcome.json',dict(status='completed',new_measurements=len(st.rows),all_validated=all(r['status']=='ok' for r in st.rows),initial=archive[0]['objective'],best=min(r['objective'] for r in archive),configs=[r['config'] for r in archive],selected=selected,limits=['single heldout tiny FIR3, one seed, no quality conclusion','nontrivial multilevel hierarchy untested','API LLM and Yosys/ABC LUT4 substitutions','not original implementation or dataset']))
print('COMPLETED',json.dumps(archive),flush=True)

