"""Read-only full-dataset schema audit. No LLM request, HDL execution or script download.

Official TaskScanner is called with all subsets/levels/modalities. The exact
load_case_files/build_task_messages function ASTs are loaded without importing
API client code or requiring openai. Official file finders/renderer are reused;
PDF text extraction uses installed PyMuPDF. This is a schema audit, not evaluation.
"""
import argparse,ast,collections,dataclasses,hashlib,json,logging,pathlib,subprocess,sys
from dataset_adapter import structural_overlay
from typing import Dict,List
p=argparse.ArgumentParser();p.add_argument('--upstream',required=True);p.add_argument('--output',required=True);a=p.parse_args()
u=pathlib.Path(a.upstream).resolve();out=pathlib.Path(a.output).resolve()
if out.exists() and any(out.iterdir()):raise SystemExit('output must be empty')
out.mkdir(parents=True)
logging.basicConfig(filename=out/'loader_feedback.log',level=logging.WARNING)
sys.path.insert(0,str(u))
from src.config import TaskScanner,Task,SUPPORTED_SUBSETS,SUPPORTED_MODALITIES,SUPPORTED_LEVELS
from src.utils import file_finder as ff
from src.utils.pdf_parser import PDFParser
from src.utils.pdf_renderer import PDFImageRenderer
from src.evaluators.eval_utils import extract_option
from src.evaluators.specom_eval import evaluate_specom
from src.evaluators.rtlfix_eval import evaluate_rtlfix
from src.evaluators.rtlfix_eval import _load_golden_fix_pair
import fitz
PIN='e875437fbb11590b71775b32d3579726d702cfc6'
def git(*args):return subprocess.check_output(['git','-C',str(u),*args],text=True).strip()
assert git('rev-parse','HEAD')==PIN
class AuditConfig:
 def __getitem__(self,key):return {'path':{'data_root':u/'data'},'evaluation':{'levels':SUPPORTED_LEVELS}}[key]
 def get_expanded_subsets(self):return SUPPORTED_SUBSETS
 def get_expanded_modalities(self):return SUPPORTED_MODALITIES

source=u/'src/llm_client.py';tree=ast.parse(source.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['load_case_files','build_task_messages']]
ns={'Task':Task,'Dict':Dict,'List':List,'PDFParser':PDFParser,'PDFImageRenderer':PDFImageRenderer,'logger':logging.getLogger('official_loader')}
ns.update({name:getattr(ff,name) for name in ['find_answer_file','find_question_file','find_rtl_file','find_svagen_rtl_file','find_spec_file','find_tb_file','extract_first_rtl_module_name','find_ref_model_file','parse_verilog_module_interface','safe_read_text']})
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
class TextPDF:
 def extract_text(self,path):
  with fitz.open(path) as pdf:return '\n'.join(page.get_text() for page in pdf)
renderer=PDFImageRenderer({'max_pages':8,'render_dpi':144});tasks=TaskScanner(AuditConfig()).generate_tasks();records=[]
required={'SpeCom':['question','answer'],'MGen':['rtl','tb','interface'],'TBGen':['rtl','spec'],'SVAGen':['rtl','spec'],'RTLFix':['question','fix_reference']}
for task in tasks:
 d=task.case_dir;key=str(d.relative_to(u/'data'));files=ns['load_case_files'](task,TextPDF(),renderer)
 row={'id':key,'official_task_id':task.task_id,'subset':task.subset,'level':task.level,'modality':task.modality,'input_files':[],'warnings':[],'errors':[]}
 for f in sorted(d.iterdir()):
  if f.is_file():row['input_files'].append({'name':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 # Audit the underlying specification independently of the loader's SpeCom Text omission.
 spec=ff.find_spec_file(d,task.modality)
 if task.subset=='SVAGen' and task.modality=='Text' and not spec:
  specs=sorted(f for f in d.glob('*.txt') if not f.name.lower().startswith(('q','ref')));spec=specs[0] if specs else None
 row['spec_path']=spec.name if spec else None
 spec_ok=bool(spec and spec.stat().st_size>0)
 if task.subset=='RTLFix' and task.modality=='Text':spec_ok='<spec>' in files['question_text'] or 'module' in files['question_text']
 if not spec_ok:row['warnings'].append('missing_or_empty_spec')
 if task.subset=='SpeCom' and task.modality=='Text' and spec_ok and not files['spec_text']:row['warnings'].append('official_loader_omits_available_text_spec')
 present={'question':bool(files['question_text'].strip()),'answer':bool(extract_option(files['answer_text'])),'rtl':bool(files['rtl_text'].strip()),'tb':bool(files['tb_text'].strip()),'interface':bool(files['ref_model_top'] and files['ref_model_ports']),'spec':spec_ok,'fix_reference':False}
 if task.subset=='RTLFix' and task.modality=='Text':
  try:
   old,new,meta=_load_golden_fix_pair(d);present['fix_reference']=True;row['fix_reference_format']=meta.get('source_format')
  except Exception as ex:row['errors'].append('invalid_fix_reference: '+str(ex))
 req=required[task.subset].copy()
 if task.subset=='RTLFix' and task.modality=='MultiModal':req=['rtl','tb','spec']
 if task.modality=='MultiModal':
  req.append('images');present['images']=bool(files['spec_image_parts'])
  row['rendered_pdf_pages']=len(files['spec_image_parts'])
  row['image_payload_hashes']=[hashlib.sha256(x['image_url']['url'].encode()).hexdigest() for x in files['spec_image_parts']]
 if task.subset=='SpeCom' and task.modality=='Text':req.append('spec')
 if task.subset=='MGen':req.append('spec')
 row['missing_required']=[k for k in dict.fromkeys(req) if not present[k]]
 # Loader populated core task contents. Prompt construction alone may still accept placeholders.
 payload_req=[k for k in req if k!='spec']
 row['payload_loadable']=all(present[k] for k in payload_req)
 row['schema_complete']=not row['missing_required']
 try:
  messages=ns['build_task_messages'](task,files);row['prompt_constructible']=True
  text=json.dumps(messages,ensure_ascii=False);row['prompt_sha256']=hashlib.sha256(text.encode()).hexdigest();row['prompt_characters']=len(text)
  row['prompt_has_missing_spec_placeholder']='[Specification file not found]' in text
  row['prompt_has_missing_rtl_placeholder']='[RTL file not found]' in text
 except Exception as ex:row.update(prompt_constructible=False,prompt_error=str(ex))
 if task.subset=='MGen':row['wrapper_mode']=files['mgen_wrapper_mode']
 # Static feature observations only; they are NOT tested backend support classifications.
 rtl=files['rtl_text'];row['static_features']=[name for name,regex in [('inout',r'\binout\b'),('include',r'`include'),('sequential',r'\b(posedge|negedge)\b'),('unknown_bits',r"\b\d*'[bBhH][0-9a-fA-F_]*[xXzZ]"),('delay',r'#\s*\d+')] if __import__('re').search(regex,rtl)]
 adapted,overlays,resolved=structural_overlay(task,files,u,ff)
 row['structural_overlays']=overlays
 row['adapted_missing_required']=[k for k in row['missing_required'] if k not in resolved]
 row['adapted_schema_complete']=not row['adapted_missing_required']
 try:
  adapted_messages=ns['build_task_messages'](task,adapted)
  row['adapted_prompt_sha256']=hashlib.sha256(json.dumps(adapted_messages,ensure_ascii=False).encode()).hexdigest()
 except Exception as ex:row['adapted_prompt_error']=str(ex)
 row['evaluation_state']='not_attempted'
 row['eda_state']='not_attempted'
 row['eda_support']='not_certified; static features are observations only'
 row['adapter_scope']='current EDA pilot adapter is case-specific; this audit does not assert general backend support'
 if task.subset=='SpeCom' or (task.subset=='RTLFix' and task.modality=='Text'):
  row['evaluation_state']='reference_scorer_executed; no model generation or RTL execution'
  if task.subset=='SpeCom':
   expected=extract_option(files['answer_text']);positive=expected or ''
   negative=next(x for x in 'ABCD' if x!=expected)
   evaluator=evaluate_specom
  else:
   try:old,new,_=_load_golden_fix_pair(d);positive=old+'\n'+new;negative=old
   except Exception:positive='';negative='???'
   evaluator=evaluate_rtlfix
  row['reference_controls']=[]
  for label,response in [('reference_positive',positive),('wrong',negative),('malformed','???')]:
   result=evaluator(d,response)
   row['reference_controls'].append({'label':label,'response':response,'response_sha256':hashlib.sha256(response.encode()).hexdigest(),'status':result.status,'functional_pass':result.functional_pass,'error_msg':result.error_msg,'semantics':'reference-only scorer check, not a live LLM result or executable repair proof'})
  row['reference_scorer_expected_positive']=row['reference_controls'][0]['status']=='pass'
  row['complete_task_reference_checked']=row['adapted_schema_complete'] and row['reference_scorer_expected_positive']
 records.append(row)

paper={'SpeCom':{'total':149,'Text':98,'MultiModal':51},'MGen':{'total':111,'Text':80,'MultiModal':31},'TBGen':{'total':158,'Text':107,'MultiModal':51},'SVAGen':{'total':61,'Text':40,'MultiModal':21},'RTLFix':{'total':268,'Text':102,'MultiModal':166}}
summary={}
for subset in SUPPORTED_SUBSETS:
 rs=[r for r in records if r['subset']==subset]
 summary[subset]={'paper':paper[subset],'directories':len(rs),'official_scanned_tasks':len(rs),'payload_loadable':sum(r['payload_loadable'] for r in rs),'prompt_constructible':sum(r['prompt_constructible'] for r in rs),'schema_complete':sum(r['schema_complete'] for r in rs),'adapted_schema_complete':sum(r['adapted_schema_complete'] for r in rs),'reference_scorer_executed':sum('reference_controls' in r for r in rs),'reference_positive_pass':sum(r.get('reference_scorer_expected_positive',False) for r in rs),'complete_task_reference_checked':sum(r.get('complete_task_reference_checked',False) for r in rs),'missing_required':dict(collections.Counter(k for r in rs for k in r['missing_required'])),'warnings':dict(collections.Counter(k for r in rs for k in r['warnings'])),'by_modality':{m:{'directories':sum(r['modality']==m for r in rs),'schema_complete':sum(r['schema_complete'] and r['modality']==m for r in rs)} for m in SUPPORTED_MODALITIES}}
 # All paper Text counts coincide, so directory deficits are localized to MultiModal.
 summary[subset]['paper_directory_deficit']=paper[subset]['total']-len(rs)
 summary[subset]['modality_deficit']={m:paper[subset][m]-sum(r['modality']==m for r in rs) for m in SUPPORTED_MODALITIES}

history=[]
for commit in git('rev-list','--all').splitlines():
 names=git('ls-tree','-r','--name-only',commit).splitlines();cases=collections.defaultdict(set)
 for name in names:
  parts=name.split('/')
  if len(parts)>=5 and parts[0]=='data':cases[parts[1]].add('/'.join(parts[:5]))
 history.append({'commit':commit,'data_tree':git('rev-parse',commit+':data'),'cases':{s:len(v) for s,v in cases.items()}})
allnames=git('ls-tree','-r','--name-only','HEAD').splitlines();testcases=sorted({ '/'.join(n.split('/')[1:5]) for n in allnames if n.startswith('test/') and len(n.split('/'))>=6})
# Correct depth is test/subset/level/modality/case/file => six segments.
primary={r['id'] for r in records};test_unique=[k for k in testcases if k not in primary]
file_comparisons=[]
for n in allnames:
 if not n.startswith('test/'):continue
 f=u/n;other=u/'data'/str(pathlib.Path(n).relative_to('test'))
 file_comparisons.append({'test_path':n,'matching_data_path_exists':other.is_file(),'identical_bytes':other.is_file() and f.read_bytes()==other.read_bytes()})
allfiles=[u/n for n in allnames if (u/n).is_file()]
report={'upstream_commit':PIN,'task_unit':'one Task per data/subset/level/modality/case directory, official TaskScanner; no per-file expansion','no_llm_calls':True,'no_eda_execution':True,'loader_provenance':{'file':'src/llm_client.py','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'exact_function_ast':[{ 'name':n.name,'start_line':n.lineno,'end_line':n.end_lineno} for n in nodes],'imports_avoided':['API client/openai'],'pdf_text_backend':'PyMuPDF structural-audit substitution','pdf_renderer':'official PDFImageRenderer, max8 pages,144dpi'},'summary':summary,'totals':{'paper':747,'directories':len(records),'scanned':len(tasks),'payload_loadable':sum(r['payload_loadable'] for r in records),'prompt_constructible':sum(r['prompt_constructible'] for r in records),'schema_complete':sum(r['schema_complete'] for r in records),'adapted_schema_complete':sum(r['adapted_schema_complete'] for r in records),'reference_scorer_executed':sum('reference_controls' in r for r in records),'reference_positive_pass':sum(r.get('reference_scorer_expected_positive',False) for r in records),'complete_task_reference_checked':sum(r.get('complete_task_reference_checked',False) for r in records),'directory_deficit':747-len(records)},'history':history,'git_checks':{'shallow':git('rev-parse','--is-shallow-repository'),'remote_refs':git('ls-remote','--heads','--tags','origin'),'fsck':git('fsck','--full','--no-reflogs'),'submodules':[n for n in git('ls-tree','-r','HEAD').splitlines() if n.startswith('160000')],'lfs_pointers':[str(f.relative_to(u)) for f in allfiles if f.stat().st_size<1024 and f.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1')],'archives':[str(f.relative_to(u)) for f in allfiles if f.suffix.lower() in ['.zip','.tar','.gz','.7z','.rar']]},'test_tree':{'case_directories':len(testcases),'additional_case_keys':test_unique,'file_comparisons':file_comparisons},'cases':records}
pilot_keys={'SpeCom/L1/Text/1 bit Full Adder using HA','MGen/L1/Text/1 bit Full Adder using HA','TBGen/L1/Text/address_mux','SVAGen/L1/Text/usbh_crc16','RTLFix/L1/MultiModal/1','RTLFix/L1/Text/1'}
for row in records:
 row['prior_pilot_input']=row['id'] in pilot_keys
 if row['prior_pilot_input'] and row['subset'] in ['MGen','TBGen','SVAGen','RTLFix'] and not(row['subset']=='RTLFix' and row['modality']=='Text'):
  row['eda_state']='bounded_prior_fixed_response_pilot_executed'
import csv
with (out/'coverage.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=['id','subset','level','modality','schema_complete','adapted_schema_complete','missing_required','adapted_missing_required','evaluation_state','eda_state','eda_support','prior_pilot_input'],lineterminator='\n');writer.writeheader()
 for row in records:writer.writerow({k:row[k] for k in writer.fieldnames})
(out/'audit.json').write_text(json.dumps(report,indent=2));(out/'summary.json').write_text(json.dumps({k:v for k,v in report.items() if k not in ['cases','test_tree']},indent=2));print(json.dumps({'summary':summary,'totals':report['totals'],'test_cases':len(testcases),'test_new_keys':test_unique},indent=2))
