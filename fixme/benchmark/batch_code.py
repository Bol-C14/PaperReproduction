"""Bounded all-code-case reference calibration, never model benchmark results.

MGen: generated C++ reference from official RTL through Verilator, official DPI
wrapper and supplied TB. TBGen: generated SV checker against a renamed copy of
source RTL, plus output perturbation negative. SVAGen: direct output-assignment
invariants only, plus true RTL mutation and constant-property control.
All substitutions and unsupported contracts are explicit per case.
"""
import argparse,ast,operator,collections,concurrent.futures,dataclasses,hashlib,json,logging,os,pathlib,re,shutil,signal,subprocess,sys,time,xml.etree.ElementTree as ET
from isolation import confine
from evaluation import command_state,property_counts,formal_score
P=argparse.ArgumentParser();P.add_argument('--upstream',required=True);P.add_argument('--tools',required=True);P.add_argument('--audit',required=True);P.add_argument('--output',required=True);P.add_argument('--limit',type=int);P.add_argument('--cases',nargs='*');P.add_argument('--workers',type=int,default=2);a=P.parse_args()
u=pathlib.Path(a.upstream).resolve();tools=pathlib.Path(a.tools).resolve();out=pathlib.Path(a.output).resolve();audit=json.loads(pathlib.Path(a.audit).read_text());out.mkdir(parents=True,exist_ok=True)
if any(out.iterdir()):raise SystemExit('output directory must be empty')
sys.path.insert(0,str(u));from src.utils import file_finder as ff
from src.evaluators.mgen_eval import MGenEvaluator
from src.utils.file_finder import VerilogModuleInterface,VerilogPort
logging.basicConfig(filename=out/'adapter_feedback.log',level=logging.WARNING)
env={'PATH':str(tools/'usr/bin')+':/usr/bin:/bin','VERILATOR_ROOT':str(tools/'usr/share/verilator'),'HOME':'/nonexistent','LANG':'C'}
rows=[r for r in audit['cases'] if r['subset'] in ['MGen','TBGen','SVAGen'] or(r['subset']=='RTLFix' and r['modality']=='MultiModal')]
if a.cases:rows=[r for r in rows if r['id'] in a.cases]
if a.limit:rows=rows[:a.limit]
def strip(s):return re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def const_value(text,bindings,seen=None):
 text=text.strip();seen=set() if seen is None else seen
 def number(m):
  radix={'b':2,'o':8,'d':10,'h':16}[m[1].lower()];return str(int(m[2].replace('_',''),radix))
 text=re.sub(r"(?:\d+)?'([bBoOdDhH])([0-9a-fA-F_]+)",number,text)
 ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.FloorDiv:operator.floordiv,ast.Div:operator.floordiv,ast.Mod:operator.mod,ast.LShift:operator.lshift,ast.RShift:operator.rshift,ast.BitOr:operator.or_,ast.BitAnd:operator.and_,ast.BitXor:operator.xor}
 def visit(n):
  if isinstance(n,ast.Constant) and isinstance(n.value,int):return n.value
  if isinstance(n,ast.Name) and n.id in bindings and n.id not in seen:return const_value(bindings[n.id],bindings,seen|{n.id})
  if isinstance(n,ast.BinOp) and type(n.op) in ops:return ops[type(n.op)](visit(n.left),visit(n.right))
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd,ast.Invert)):
   val=visit(n.operand);return -val if isinstance(n.op,ast.USub) else (~val if isinstance(n.op,ast.Invert) else val)
  raise ValueError('parameter expression outside bounded constant grammar')
 val=visit(ast.parse(text,mode='eval').body)
 if not -1048576<=val<=1048576:raise ValueError('parameter outside bound')
 return val

class Case:
 def __init__(self,row):
  self.row=row;self.dir=u/'data'/row['id'];self.w=out/row['subset']/('case_'+hashlib.sha256(row['id'].encode()).hexdigest()[:12]);self.w.mkdir(parents=True);self.events=[];self.started=time.monotonic();self.result={'id':row['id'],'subset':row['subset'],'input_files':row['input_files'],'overlays':row['structural_overlays'],'live_llm':False,'kind':'reference-calibration-not-model-score','fidelity':'structural-substituted','functional_pass':None,'negative_control_detected':None,'commands':0,'status':'not_attempted'}
 def command(self,cmd,label,timeout=30):
  remaining=150-(time.monotonic()-self.started)
  if remaining<=0:return {'status':'timeout','returncode':None},'case budget exhausted'
  timeout=min(timeout,remaining);i=len(self.events);log=self.w/f'{i:02d}_{label}.log';e={'index':i,'command':list(map(str,cmd)),'cwd':str(self.w.relative_to(out)),'log':str(log.relative_to(out)),'timeout_seconds':timeout,'isolation':'sanitized env, process group, rlimits, seccomp no-network; FS confinement unavailable; static source allowlist'};t=time.monotonic()
  try:
   with log.open('wb') as handle:
    proc=subprocess.Popen(cmd,cwd=self.w,env=dict(env,TMPDIR=str(self.w)),stdout=handle,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=confine)
    try:e.update(returncode=proc.wait(timeout),status='completed')
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait();e.update(returncode=None,status='timeout')
  except Exception as ex:e.update(status='error',returncode=None,error=str(ex));log.write_text(str(ex))
  e['seconds']=round(time.monotonic()-t,3);self.events.append(e);return e,log.read_text(errors='replace')
 def stop(self,status,reason):self.result.update(status=status,reason=reason);return False
 def check(self,event,log,phase='compile'):
  status,reason=command_state(event,log,phase)
  if status:
   if status=='fail':status='error';reason='official reference/derived baseline diagnostic: '+reason
   return self.stop(status,reason)
  return True
 def stage(self):
  srcs=[]
  for f in self.dir.iterdir():
   if f.suffix.lower() not in ['.v','.sv']:continue
   text=f.read_text(errors='replace');clean=strip(text)
   if re.search(r'\$(system|c\b)|import\s+"DPI|`verilator',clean):return self.stop('adapter_unsupported','source requests process/foreign-code execution outside reviewed fixture contract')
   calls=re.findall(r'\$(readmemh|readmemb|fopen|fread|fwrite|writememh|writememb)\s*\(([^;]*)',clean)
   if calls:
    read_paths=[];dynamic_read=False;safe_writes=False
    for kind,args in calls:
     quoted=re.findall(r'"([^\"]+)"',args)
     if kind in ['readmemh','readmemb']:
      if quoted:read_paths.append(quoted[0])
      else:dynamic_read=True
     elif kind=='fopen':
      if not quoted:return self.stop('adapter_unsupported','dynamic fopen path cannot be confined by this host')
      name=quoted[0];mode=quoted[1] if len(quoted)>1 else 'w'
      if mode.startswith('r'):read_paths.append(name)
      elif pathlib.Path(name).name==name and '..' not in name:safe_writes=True
      else:return self.stop('adapter_unsupported','output fopen path outside basename-only contract')
     elif kind in ['fread','fwrite'] and not any(c[0]=='fopen' for c in calls):
      return self.stop('adapter_unsupported','unbound file handle outside reviewed fixture contract')
     elif kind.startswith('writemem'):return self.stop('adapter_unsupported','memory file output outside bounded fixture contract')
    missing=sorted(set(name for name in read_paths if not(self.dir/name).is_file()))
    if missing:return self.stop('error','missing external input asset: '+str(missing))
    if dynamic_read:return self.stop('adapter_unsupported','dynamic read-file path outside reviewed dependency contract')
    if read_paths:
     for name in sorted(set(read_paths)):
      if pathlib.Path(name).name!=name:return self.stop('adapter_unsupported','non-basename read dependency outside case boundary')
      dependency_file=self.dir/name
      if name not in {x['name'] for x in self.row['input_files']}:return self.stop('error','read asset missing from immutable input manifest')
      shutil.copy2(dependency_file,self.w/name)
     self.result['staged_read_dependencies']=[{'name':name,'sha256':sha(self.dir/name)} for name in sorted(set(read_paths))]

    if safe_writes:self.result['file_io_contract']='constant basename-only output file; private cwd, file-size limit; no filesystem sandbox claim'
   for inc in re.findall(r'`include\s+"([^"]+)"',clean):
    if not (self.dir/inc).is_file():return self.stop('error','missing include asset: '+inc)
    return self.stop('adapter_unsupported','include-bearing source requires reviewed dependency staging')
   if any(p.startswith('/') or '..' in pathlib.Path(p).parts for p in re.findall(r'\$dumpfile\s*\(\s*"([^"]+)"',clean)):return self.stop('adapter_unsupported','waveform path escapes case working directory')
   target=self.w/f.name;target.write_text(text if '`timescale' in text else '`timescale 1ns/1ps\n'+text);srcs.append(target)
  self.srcs=srcs;return True
 def rtl(self):
  if self.row['subset']=='SVAGen':f=ff.find_svagen_rtl_file(self.dir)
  else:f=ff.find_rtl_file(self.dir)
  if not f:
   repairs=[o for o in self.row['structural_overlays'] if o['field']=='rtl_text']
   if repairs:f=u/repairs[0]['source'];assert sha(f)==repairs[0]['sha256']
  return self.w/f.name if f else None
 def interface(self,src,top):
  e,log=self.command([str(tools/'usr/bin/verilator'),'--xml-only','--timing','-Wno-fatal','--top-module',top,'--xml-output','interface.xml',str(src)],'interface',15)
  if not self.check(e,log):return None
  tree=ET.parse(self.w/'interface.xml');mod=tree.find(".//module[@topModule='1']");types={x.get('id'):x for x in tree.findall('.//typetable/*')};ports=[]
  if mod is None:self.stop('error','interface export contains no top');return None
  for var in mod.findall('var'):
   if var.get('dir') not in ['input','output','inout']:continue
   dt=types.get(var.get('dtype_id'))
   if dt is None or dt.tag!='basicdtype':self.stop('adapter_unsupported','array/complex port type outside scalar/vector fixture generator');return None
   width=abs(int(dt.get('left','0'))-int(dt.get('right','0')))+1
   if width>256:self.stop('adapter_unsupported','port width exceeds 256-bit bounded stimulus contract');return None
   ports.append({'name':var.get('origName') or var.get('name'),'direction':var.get('dir'),'width':width})
  if not ports or not any(p['direction']=='output' for p in ports):self.stop('adapter_unsupported','no usable observable output interface');return None
  if any(p['direction']=='inout' for p in ports):self.stop('adapter_unsupported','bidirectional port stimulus/drive semantics not implemented');return None
  (self.w/'ports.json').write_text(json.dumps(ports,indent=2));return ports
 def ivsim(self,files,top,label):
  e,log=self.command([str(tools/'usr/bin/iverilog'),'-B',str(tools/'usr/lib/x86_64-linux-gnu/ivl'),'-g2012','-s',top,'-o',label+'.vvp',*map(str,files)],label+'_compile',20)
  if not self.check(e,log):return None,None
  return self.command([str(tools/'usr/bin/vvp'),label+'.vvp'],label+'_simulate',2)
 def marker_score(self,e,log):
  if not e:return None
  status,reason=command_state(e,log,'simulation')
  if status:return status
  match=re.search(r'CALIBRATION checks=(\d+) failures=(\d+) unknown=(\d+)',log)
  if not match:return 'unknown'
  checks,bad,unknown=map(int,match.groups());self.result['observed_checks']=checks;self.result['observed_unknown']=unknown
  if unknown or not checks:return 'unknown'
  return 'fail' if bad else 'pass'
 def tbgen(self):
  src=self.rtl()
  if not src:return self.stop('error','missing RTL asset')
  if re.search(r'\$(u?random)',strip(src.read_text())):return self.stop('adapter_unsupported','internal source randomness has independent state across cloned RTL instances; deterministic oracle contract unavailable')
  names=ff.extract_verilog_module_names(src.read_text());top=names[0] if names else ''
  if not top:return self.stop('error','no RTL module declaration')
  ports=self.interface(src,top)
  if not ports:return
  # Renamed *top* only, retaining helper modules from the original source.
  text=src.read_text();pat=r'\bmodule\s+'+re.escape(top)+r'\b';renamed=re.sub(pat,'module oracle_'+top,text,count=1)
  # Helper modules would otherwise be multiply defined by including the full file twice.
  blocks=re.findall(r'\bmodule\b.*?\bendmodule\b',renamed,re.S)
  oracle=next((b for b in blocks if re.match(r'module\s+oracle_'+re.escape(top)+r'\b',b)),None)
  if not oracle:return self.stop('error','could not isolate oracle top')
  (self.w/'oracle.sv').write_text('`timescale 1ns/1ps\n'+oracle)
  if any(p['name'].startswith('__cal_') for p in ports):return self.stop('adapter_unsupported','DUT port collides with reserved harness namespace')
  ins=[p for p in ports if p['direction']=='input'];outs=[p for p in ports if p['direction']=='output']
  clocks=[p for p in ins if re.search(r'(^|_)(clk|clock|gclk)(_|$)|clk$',p['name'],re.I)]
  if len(clocks)>1:return self.stop('adapter_unsupported','multiple clocks require per-case timing contract')
  clock=clocks[0]['name'] if clocks else None
  if (clocks and clocks[0]['width']!=1) or (not clock and re.search(r'\b(posedge|negedge)\b',strip(src.read_text()))):return self.stop('adapter_unsupported','clock identification/width outside bounded stimulus contract')
  decl=[]
  for p in ports:
   width=f"[{p['width']-1}:0] " if p['width']>1 else ''
   decl.append(('reg ' if p['direction']=='input' else 'wire ')+width+p['name']+';')
   if p['direction']=='output':decl.append('wire '+width+'ref_'+p['name']+';')
  conn=lambda prefix:', '.join('.'+p['name']+'('+('ref_' if p['direction']=='output' and prefix else '')+p['name']+')' for p in ports)
  resets=[p for p in ins if re.search(r'(^|_)(rst|reset|resetn|rstn)(_|$)|rst_n$|reset_n$',p['name'],re.I)]
  active={p['name']:0 if re.search(r'(_n$|n$|_b$)',p['name']) else 1 for p in resets}
  init='\n'.join(p['name']+' = '+str(active.get(p['name'],0))+';' for p in ins)
  release='\n'.join(n+' = '+str(1-v)+';' for n,v in active.items())
  drive='\n'.join(p['name']+' = {$random(__cal_seed),$random(__cal_seed),$random(__cal_seed),$random(__cal_seed),$random(__cal_seed),$random(__cal_seed),$random(__cal_seed),$random(__cal_seed)};' for p in ins if p['name']!=clock and p['name'] not in active)
  golden='{'+','.join('ref_'+p['name'] for p in outs)+'}';actual='{'+','.join(p['name'] for p in outs)+'}'
  # The response is an authored checker fixture, not an LLM testbench and not spec coverage.
  sample=f"if ((^{golden}) === 1'bx || (^{actual}) === 1'bx) __cal_unknowns=__cal_unknowns+1; else begin __cal_checks=__cal_checks+1; if ({actual} !== {golden}) __cal_failures=__cal_failures+1; end"
  tb='\n'.join(['`timescale 1ns/1ps','module calibration_tb;',*decl,'integer __cal_seed=13579; integer __cal_i; integer __cal_checks=0;integer __cal_failures=0;integer __cal_unknowns=0;',top+' dut('+conn(False)+');','oracle_'+top+' golden('+conn(True)+');','initial begin',init,'#2;',release,'for(__cal_i=0;__cal_i<64;__cal_i=__cal_i+1) begin',drive,('#2; '+clock+'=1; #2;' if clock else '#2;'),sample,(clock+'=0;' if clock else ''),'end','$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",__cal_checks,__cal_failures,__cal_unknowns); $finish; end','endmodule'])
  (self.w/'response_positive.sv').write_text(tb)
  self.result['stimulus_contract']={'seed':13579,'cycles':64,'clock':clock,'reset_polarities':active,'unknown_handling':'any observed unknown prevents pass','oracle':'renamed copy of supplied RTL; self-consistency/calibration only'}
  e,log=self.ivsim([src,self.w/'oracle.sv',self.w/'response_positive.sv'],'calibration_tb','positive');baseline=self.marker_score(e,log)
  if baseline is None:return
  self.result['reference_status']=baseline
  if baseline!='pass':return self.stop('error' if baseline=='fail' else baseline,'reference calibration did not establish a known, matching baseline')
  # Perturb one checked output bit inside checker; content changes, no name-based verdict.
  neg=tb.replace(actual+' !== '+golden,actual+" !== ("+golden+" ^ 1'b1)")
  (self.w/'response_negative.sv').write_text(neg)
  e,log=self.ivsim([src,self.w/'oracle.sv',self.w/'response_negative.sv'],'calibration_tb','negative');negative=self.marker_score(e,log)
  self.result.update(negative_status=negative,negative_control_detected=negative=='fail',status='pass' if negative=='fail' else (negative if negative in ['unknown','error'] else 'error'),functional_pass=True if negative=='fail' else None,reason='reference/checker positive and perturbed-checker negative executed')
 def mgen(self):
  ev=MGenEvaluator(self.w,None,{})
  interface,mode,interface_path=ev._select_wrapper_interface(self.dir)
  if not interface or not interface.ports:return self.stop('adapter_unsupported','official DPI interface parser has no usable ports')
  if any(p.direction=='inout' for p in interface.ports):return self.stop('adapter_unsupported','official longint DPI inout contract not ported')
  src=self.w/interface_path.name
  if re.search(r'#\s*\d+',strip(src.read_text())):return self.stop('adapter_unsupported','timed source reference needs explicit submodel time advancement')
  if re.search(r"\b\d*'[bBhH][0-9a-fA-F_]*[xXzZ]",strip(src.read_text())):return self.stop('adapter_unsupported','explicit X/Z source semantics outside two-state compiled reference contract')
  self.result.update(wrapper_mode=mode,reference_source=interface_path.name,reference_source_sha256=sha(interface_path),semantic_contract='two-state compiled reference; official DPI wrapper and supplied testbench; no model sampling')
  tb_path=ff.find_tb_file(self.dir)
  if not tb_path:return self.stop('error','missing golden testbench')
  tb_clean=strip(tb_path.read_text())
  binding_match=re.search(r'\b'+re.escape(interface.name)+r'\s*#\s*\((.*?)\)\s+\w+\s*\(',tb_clean,re.S)
  params={};param_args=[]
  if binding_match:
   pairs=re.findall(r'\.([A-Za-z_]\w*)\s*\(([^()]*)\)',binding_match[1])
   if not pairs:return self.stop('adapter_unsupported','positional/complex parameter bindings need explicit elaboration adapter')
   bindings=dict(re.findall(r'\b(?:localparam|parameter)\s+(?:integer\s+)?(\w+)\s*=\s*([^;,]+)',tb_clean))
   try:params={name:const_value(value,bindings) for name,value in pairs}
   except Exception as ex:return self.stop('adapter_unsupported','unresolved reference TB parameter: '+str(ex))
   param_args=['-G'+name+'='+str(value) for name,value in params.items()]
  self.result['resolved_tb_parameters']=params
  cmd=[str(tools/'usr/bin/verilator'),'--cc','--timing','-Wno-fatal','--prefix','RefModel','--top-module',interface.name,'--Mdir','ref_obj',*param_args,str(src)]
  e,log=self.command(cmd,'reference_cpp_emit',20)
  if not self.check(e,log):return
  header=(self.w/'ref_obj/RefModel.h').read_text();meta={m[0]:int(m[1])+1 for m in re.findall(r'VL_(?:IN|OUT)(?:8|16|64|W)?\s*\(\s*&?(\w+)\s*,\s*(\d+)\s*,\s*0(?:\s*,\s*\d+)?\s*\)',header)}
  if any(p.name not in meta or meta[p.name]>64 for p in interface.ports):return self.stop('adapter_unsupported','DPI requires scalar/vector <=64-bit resolved ports; complex or wider port found')
  # Resolve parameter widths using actual compiled interface, not guessed expressions.
  normalized=VerilogModuleInterface(interface.name,[VerilogPort(p.name,p.direction,f'[{meta[p.name]-1}:0]' if meta[p.name]>1 else '') for p in interface.ports],['parameter '+name+' = '+str(value) for name,value in params.items()])
  wrapper=ev._generate_wrapper(normalized);(self.w/'ref_wrapper.sv').write_text(wrapper)
  e,log=self.command(['/usr/bin/make','-C','ref_obj','-f','RefModel.mk','-j1'],'reference_cpp_build',45)
  if not self.check(e,log):return
  args=[];body=[]
  for p in interface.ports:
   if p.direction=='input':args.append('unsigned long long '+p.name);body.append('model.'+p.name+'='+p.name+';')
   else:args.append('unsigned long long* '+p.name)
  body.append('model.eval();')
  for p in interface.ports:
   if p.direction=='output':body.append('*'+p.name+'=model.'+p.name+';')
  cpp='#include "RefModel.h"\nextern "C" void ref_model_eval('+','.join(args)+'){static VerilatedContext context;static RefModel model(&context);'+''.join(body)+'}\n';(self.w/'response.cpp').write_text(cpp)
  tb=ff.find_tb_file(self.dir)
  if not tb:return self.stop('error','missing golden testbench')
  tbtext=(self.w/tb.name).read_text();counter=bool(re.search(r'integer[^;]*\btotal_tests\b',strip(tbtext)) and re.search(r'integer[^;]*\bfailed_tests\b',strip(tbtext)))
  if counter:tbtext=tbtext.replace('$finish', '$display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish')
  (self.w/'golden_tb.sv').write_text(tbtext);top=ev._parse_tb_top(tbtext)
  rtl=ff.find_rtl_file(self.dir);files=[str(self.w/'ref_wrapper.sv'),str(self.w/'golden_tb.sv')]
  if rtl and mode=='reference_model' and rtl!=interface_path:files.insert(0,str(self.w/rtl.name))
  archive=self.w/'ref_obj/libRefModel.a'
  if not archive.is_file():archive=self.w/'ref_obj/RefModel__ALL.a'
  if not archive.is_file():return self.stop('error','generated reference archive missing')
  def dpi(label):
   cmd=[str(tools/'usr/bin/verilator'),'--binary','--timing','-Wno-fatal','--top-module',top,'--Mdir','dpi_obj','-CFLAGS','-I'+str(self.w/'ref_obj'),'-LDFLAGS',str(archive),*files,str(self.w/'response.cpp')]
   e,log=self.command(cmd,label+'_compile',50)
   if not self.check(e,log):return None,None
   return self.command([str(self.w/'dpi_obj'/('V'+top))],label+'_simulate',3)
  def score(e,log):
   if not e:return None
   status,_=command_state(e,log,'simulation')
   if status:return status
   reports=re.findall(r'HARNESS_COUNTS checks=(\d+) failures=(\d+)',log)
   if reports:checks,bad=map(int,reports[-1]);self.result['observed_checks']=checks;return 'pass' if checks>0 and bad==0 else ('fail' if bad else 'unknown')
   checks=len(re.findall(r'Test case Passed',log,re.I));bad=bool(re.search(r'Test case Failed|TEST_FAIL|mismatch|FATAL',log,re.I));self.result['observed_checks']=checks
   return 'fail' if bad else ('pass' if checks>0 else 'unknown')
  e,log=dpi('positive');positive=score(e,log)
  if positive is None:return
  self.result['reference_status']=positive
  if positive!='pass':return self.stop('error' if positive=='fail' else positive,'official golden TB/C++ derived baseline did not establish explicit successful checks')
  target=next(p.name for p in interface.ports if p.direction=='output');negative=cpp.replace('*'+target+'=model.'+target+';','*'+target+'=model.'+target+' ^ 1ULL;');(self.w/'response.cpp').write_text(negative);(self.w/'response_positive.cpp').write_text(cpp)
  e,log=dpi('negative');ns=score(e,log);self.result.update(negative_status=ns,negative_control_detected=ns=='fail',status='pass' if ns=='fail' else(ns if ns in ['unknown','error'] else 'unknown'),functional_pass=True if ns=='fail' else None,reason='generated reference C++/DPI golden-TB calibration and output-bit negative')
 def svagen(self):
  src=self.rtl()
  if not src:return self.stop('error','missing RTL')
  code=src.read_text();clean=re.sub(r'/\*.*?\*/|//[^\n]*',lambda m: ''.join('\n' if c=='\n' else ' ' for c in m[0]),code,flags=re.S);names=ff.extract_verilog_module_names(code);top=names[0] if names else ''
  interface=ff.parse_verilog_module_interface(code,top)
  if not interface:return self.stop('adapter_unsupported','no parsed module/port interface for invariant fixture generation')
  outputs={p.name for p in interface.ports if p.direction=='output'}
  relations=[m for m in re.finditer(r'\bassign\s+(\w+(?:\[[^\]]+\])?)\s*=\s*([^;]+);',clean) if re.match(r'\w+',m[1])[0] in outputs]
  relation=relations[0] if relations else None
  if relation and sum(m[1]==relation[1] for m in relations)>1:
   e,xml_log=self.command([str(tools/'usr/bin/verilator'),'--xml-only','--timing','-Wno-fatal','--top-module',top,'--xml-output','active_driver.xml',str(src)],'active_driver',15)
   if not self.check(e,xml_log):return
   xml=ET.parse(self.w/'active_driver.xml');mod=xml.find(".//module[@topModule='1']")
   lines={int(x.get('loc').split(',')[1]) for x in mod.findall('contassign') if x.get('loc')}
   active=[m for m in relations if any(clean[:m.start()].count('\n')+1<=line<=clean[:m.end()].count('\n')+1 for line in lines)]
   if not active:return self.stop('adapter_unsupported','multiple generated drivers could not be mapped to elaborated active assignment')
   relation=active[0];self.result['active_assignment_line']=clean[:relation.start()].count('\n')+1

  if relation is None:return self.stop('adapter_unsupported','no direct continuous output assignment: temporal/reference-property generation outside implemented adapter contract')
  lhs,rhs=relation[1],relation[2]
  if re.search(r"\b\d*'[bBhH][0-9a-fA-F_]*[xXzZ]",rhs):return self.stop('adapter_unsupported','selected output relation depends on explicit X/Z')
  parameters=dict(re.findall(r'\b(?:localparam|parameter)\s+(?:integer\s+)?(\w+)\s*=\s*([^;,]+)',clean))
  port=next(p for p in interface.ports if p.name==re.match(r'\w+',lhs)[0])
  selection=re.search(r'\[([^\]]+)\]',lhs)
  width_expr=selection[1] if selection else (port.width[1:-1] if port.width else '0')
  try:
   if ':' in width_expr:left,right=width_expr.split(':');width=abs(const_value(left,parameters)-const_value(right,parameters))+1
   else:width=1
  except Exception as ex:return self.stop('adapter_unsupported','unresolved invariant target width: '+str(ex))
  assertion=f"always @* assert(({lhs}) == {width}'({rhs}));"
  self.result['assignment_target_width']=width
  self.result.update(assertion=assertion,proof_scope='two-timeframe SAT of source-derived output invariant; not full spec/SVA coverage; no environment assumptions',relation_lhs=lhs)
  def prove(source,prop,label):
   final=source.rfind('endmodule');combined=source[:final]+prop+'\n'+source[final:];p=self.w/(label+'.sv');p.write_text(combined)
   cmd=[str(tools/'usr/bin/yosys'),'-Q','-T','-p',f'read_verilog -formal -sv {p.name}; hierarchy -top {top}; prep -top {top}; flatten; async2sync; dffunmap; memory_map; opt_clean; chformal -lower; write_json {label}.json; sat -seq 2 -timeout 5 -prove-asserts -verify -show-inputs -show-outputs']
   e,log=self.command(cmd,label,15)
   try:counts=property_counts(self.w/(label+'.json'))
   except Exception:counts=None
   return e,log,counts
  e,log,counts=prove(code,assertion,'positive');self.result['property_counts']=counts;status,reason=command_state(e,log,'formal')
  if status:return self.stop('error' if status=='fail' else status,'reference proof baseline: '+reason)
  if not counts or not counts['assert'] or 'SUCCESS!' not in log:return self.stop('unknown','actual nonzero successful proof not established')
  # Actual RTL output assignment mutation while leaving the assertion unchanged.
  mutated=code[:relation.start()]+f'assign {lhs} = ~({rhs});'+code[relation.end():]
  if mutated==code:return self.stop('error','assignment mutation anchor does not match original source')
  me,mlog,mc=prove(mutated,assertion,'negative_rtl');ms,mreason=command_state(me,mlog,'formal');killed=ms=='fail' and 'proof did fail' in mlog.lower()
  ve,vlog,vc=prove(code,'always @* assert(1);','constant_control')
  cme,cmlog,cmc=prove(mutated,'always @* assert(1);','constant_mutant_control')
  cms,_=command_state(cme,cmlog,'formal');constant_killed=cms=='fail' and 'proof did fail' in cmlog.lower()
  vscore=formal_score(ve,vlog,vc,constant_killed)
  self.result.update(constant_mutation_status=cms or 'completed',constant_mutation_killed=constant_killed)
  self.result.update(negative_status=ms or 'completed',negative_control_detected=killed,constant_control_status=vscore['status'])
  if ms in ['unknown','error']:return self.stop(ms,'mutation proof: '+mreason)
  self.result.update(formal_score(e,log,counts,killed))
 def rtlfix(self):
  src=self.rtl();tb=ff.find_tb_file(self.dir)
  if not src or not tb:return self.stop('error','missing RTLFix RTL/TB')
  # Existing reviewed fixed response, resolved by actual buggy expression rather than case label.
  code=src.read_text()
  if ': ~mux1_out' not in code:return self.stop('adapter_unsupported','no reviewed fixed repair response for this MM case')
  (self.w/'repair.sv').write_text(code.replace(': ~mux1_out',': mux1_out'))
  e,log=self.ivsim([self.w/'repair.sv',self.w/tb.name],'tb_top','positive')
  if not e:return
  status,_=command_state(e,log,'simulation')
  if status:return self.stop(status,'repair simulation infrastructure/diagnostic')
  passed='ALL TESTS PASSED' in log and 'ERROR:' not in log
  if not passed:return self.stop('error','known repair did not pass golden TB')
  e,nlog=self.ivsim([src,self.w/tb.name],'tb_top','negative')
  if not e:return
  ns,_=command_state(e,nlog,'simulation');killed=ns=='fail' or(ns is None and 'ERROR:' in nlog and 'SOME TESTS FAILED' in nlog)
  self.result.update(status='pass' if killed else 'error',functional_pass=True if killed else None,negative_control_detected=killed,reason='reviewed repair and original buggy source both executed against golden TB')
 def execute(self):
  self.started=time.monotonic()  # budget starts when worker executes, not while queued
  try:
   for f in self.row['input_files']:assert sha(self.dir/f['name'])==f['sha256']
   for overlay in self.row['structural_overlays']:assert sha(u/overlay['source'])==overlay['sha256']
   if self.stage():getattr(self,self.row['subset'].lower())()
  except Exception as ex:self.result.update(status='error',reason=type(ex).__name__+': '+str(ex))
  self.result.update(commands=len(self.events),seconds=round(time.monotonic()-self.started,3));(self.w/'result.json').write_text(json.dumps(self.result,indent=2));(self.w/'trace.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in self.events));return self.result
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=min(a.workers,2)) as pool:
 future={pool.submit(Case(row).execute):row for row in rows}
 for f in concurrent.futures.as_completed(future):
  result=f.result();results.append(result);print(json.dumps({'completed':len(results),'total':len(rows),'id':result['id'],'status':result['status'],'reason':result.get('reason','')}),flush=True)
summary={'kind':'reference-calibration-not-model-score','live_llm':False,'case_count':len(results),'max_workers':min(a.workers,2),'case_budget_seconds':150,'results':sorted(results,key=lambda r:r['id']),'statuses':dict(collections.Counter(r['status'] for r in results))}
(out/'results.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary['statuses']),flush=True)
