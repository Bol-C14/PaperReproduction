"""Execute the frozen four-design validity pilot. No API, shell or arbitrary inputs."""
import argparse,collections,concurrent.futures,difflib,hashlib,json,os,pathlib,re,resource,random,signal,subprocess,sys,threading,time
from isolation import confine
from mgen_support import CONTEXT_GUARD_CPP,mgen_score
from evaluation import command_state,property_counts
P=argparse.ArgumentParser();P.add_argument('--upstream',required=True);P.add_argument('--tools',required=True);P.add_argument('--output',required=True);P.add_argument('--tb-only',action='store_true');a=P.parse_args()
u=pathlib.Path(a.upstream).resolve();tools=pathlib.Path(a.tools).resolve();out=pathlib.Path(a.output).resolve();repo=pathlib.Path(__file__).resolve().parents[2]
planfile=repo/'fixme/evaluator_validity/plan.json';plan=json.loads(planfile.read_text());planhash=hashlib.sha256(planfile.read_bytes()).hexdigest()
assert planhash=='d59c78ae9f8c633ff5f8c74d3d466e859ca3afa3e79685c9a6150e092e7dcc68'
if out.exists() and any(out.iterdir()):raise SystemExit('output must be empty')
out.mkdir(parents=True,mode=0o700);started=time.monotonic();events=[];lock=threading.Lock();count=0
sys.path.insert(0,str(u));from src.utils import file_finder as ff
from src.utils.file_finder import VerilogModuleInterface,VerilogPort
from src.evaluators.mgen_eval import MGenEvaluator
from src.simulation.vcs_runner import VCSRunner
pin=subprocess.check_output(['git','-C',str(u),'rev-parse','HEAD'],text=True).strip();assert pin==plan['upstream_commit']
manifest=json.loads((repo/'fixme/evidence/dataset_manifest.json').read_text());known={x['id']:x for x in manifest['cases']}
for id in plan['designs']:
 for f in known[id]['files']:
  p=u/'data'/id/f['name'];assert p.stat().st_size==f['size'] and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
ENV={'PATH':str(tools/'usr/bin')+':/usr/bin:/bin','HOME':'/nonexistent','LANG':'C','TMPDIR':str(out),'VERILATOR_ROOT':str(tools/'usr/share/verilator'),'PYTHONDONTWRITEBYTECODE':'1'}
def child_policy():
 confine()
 lim=plan['child_limits'];resource.setrlimit(resource.RLIMIT_CPU,(lim['cpu_seconds'],lim['cpu_seconds']));resource.setrlimit(resource.RLIMIT_AS,(lim['address_space_bytes'],lim['address_space_bytes']));resource.setrlimit(resource.RLIMIT_FSIZE,(lim['file_bytes'],lim['file_bytes']));resource.setrlimit(resource.RLIMIT_NOFILE,(lim['open_fds'],lim['open_fds']))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def work(key):
 p=out/'cases'/('c_'+hashlib.sha256(key.encode()).hexdigest()[:16]);p.mkdir(parents=True,exist_ok=True,mode=0o700);return p
def run(cmd,w,label,timeout,bindings=None):
 global count
 with lock:
  index=count;count+=1
 elapsed=time.monotonic()-started;log=w/f'{index:03d}_{label}.log';e={'index':index,'command':list(map(str,cmd)),'cwd':str(w.relative_to(out)),'log':str(log.relative_to(out)),'timeout_seconds':min(timeout,max(.01,plan['max_round_wall_seconds']-elapsed)),'input_bindings':bindings or {},'credential_environment':'allowlist only; no inherited API/connector credentials','filesystem_boundary':'no host FS sandbox; reviewed fixed recipes only'}
 if index>=plan['max_supervised_commands'] or elapsed>=plan['max_round_wall_seconds']:
  e.update(status='not_run_budget',returncode=None,seconds=0);log.write_text('preregistered round budget exhausted');events.append(e);return e,log.read_text()
 t=time.monotonic()
 try:
  with log.open('wb') as f:
   p=subprocess.Popen(cmd,cwd=w,env=dict(ENV,TMPDIR=str(w)),stdout=f,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True,preexec_fn=child_policy)
   try:e.update(status='completed',returncode=p.wait(timeout=e['timeout_seconds']))
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();e.update(status='timeout',returncode=None)
 except Exception as ex:e.update(status='error',returncode=None,error=str(ex));log.write_text(str(ex))
 e['seconds']=round(time.monotonic()-t,4)
 with lock:events.append(e);(out/'trace.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in sorted(events,key=lambda x:x['index'])))
 return e,log.read_text(errors='replace')
def execution_state(e,log,phase):
 if e['status']=='not_run_budget':return 'not_run_budget'
 if re.search(r'file size limit exceeded|out of memory|virtual memory exhausted|bad_alloc',log,re.I):return 'unknown'
 state,_=command_state(e,log,phase);return state

def upstream_parser(e,log,w):
 if e['status']!='completed':return None
 probe=w/'parser_only';probe.mkdir(exist_ok=True);(probe/'simv').write_text('not executed: parser replay only')
 simulator=VCSRunner({});simulator._run_command=lambda *args,**kwargs:(e['returncode'],log,'')
 success,_,details=simulator.run_simulation(probe)
 return {'success':success,'details':details,'mode':'exact pinned VCSRunner method on captured free-simulator log; no VCS execution'}
def outcome(e,log,kind='checker'):
 st=execution_state(e,log,'simulation')
 if st:return {'status':st,'checks':None,'failures':None,'unknown_values':None}
 if kind=='official_mux':
  passed='ALL TESTS PASSED' in log
  total=re.search(r'Total Tests:\s*(\d+)',log);bad=re.search(r'Failed:\s*(\d+)',log)
  return {'status':'pass' if passed else 'fail','checks':int(total[1]) if total else None,'failures':int(bad[1]) if bad else None,'unknown_values':None,'official_predicate':'returncode == 0 and required ALL TESTS PASSED marker'}
 m=re.search(r'VALIDITY_CHECKS checks=(\d+) failures=(\d+) unknown=(\d+)',log)
 if not m:return {'status':'unknown','checks':None,'failures':None,'unknown_values':None}
 checks,bad,unknown=map(int,m.groups())
 return {'status':'unknown' if unknown or not checks else ('fail' if bad else 'pass'),'checks':checks,'failures':bad,'unknown_values':unknown}
def diff_write(w,name,before,after):
 p=w/name;p.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original',tofile='candidate')));return {'path':str(p.relative_to(out)),'sha256':digest(p)}
results=[]
def save(row,w):
 (w/'result.json').write_text(json.dumps(row,indent=2))
 with lock:
  results.append(row);(out/'results_incremental.json').write_text(json.dumps(results,indent=2))
 print(json.dumps({'completed_trials':len(results),'family':row['family'],'variant':row['variant'],'backend':row.get('backend'),'oracle':row.get('oracle'),'status':row['decision']['status']}),flush=True)

def isolation_probes():
 w=work('isolation');canary=out/'owned_sibling_canary.txt';canary.write_text('synthetic, non-sensitive task-owned canary')
 code='import os,socket,resource,json; r={"synthetic_env_absent":"VALIDITY_SYNTHETIC_CANARY" not in os.environ,"as_limit":resource.getrlimit(resource.RLIMIT_AS)[0],"file_limit":resource.getrlimit(resource.RLIMIT_FSIZE)[0]};\ntry: socket.socket();r["network_denied"]=False\nexcept PermissionError:r["network_denied"]=True\np='+repr(str(canary))+'\ntry:\n r["sibling_read_allowed"]=bool(open(p).read());open(p,"a").write("\\nprobe");r["sibling_write_allowed"]=True\nexcept OSError:r["sibling_write_allowed"]=False\nprint(json.dumps(r))'
 os.environ['VALIDITY_SYNTHETIC_CANARY']='not-a-real-credential'
 e,log=run([sys.executable,'-c',code],w,'boundary_probe',3);os.environ.pop('VALIDITY_SYNTHETIC_CANARY',None)
 report={'event':e,'probe':json.loads(log) if e.get('returncode')==0 else {'error':log},'host_configuration_changed':False,'threat_model':'only reviewed pinned source and fixed mutations; arbitrary untrusted execution prohibited'}
 assert report['probe'].get('synthetic_env_absent') and report['probe'].get('network_denied'),report
 (out/'isolation.json').write_text(json.dumps(report,indent=2))

def simulate(src,tb,backend,w):
 (w/'input.sv').write_text(src);(w/'bench.sv').write_text(tb);bindings={n:{'sha256':digest(w/n),'artifact':str((w/n).relative_to(out))} for n in ['input.sv','bench.sv']}
 if backend=='icarus':cmd=[str(tools/'usr/bin/iverilog'),'-B',str(tools/'usr/lib/x86_64-linux-gnu/ivl'),'-g2012','-s','calibration_tb','-o','simulation.vvp','input.sv','bench.sv']
 else:cmd=[str(tools/'usr/bin/verilator'),'--binary','--timing','-Wno-fatal','--top-module','calibration_tb','--Mdir','obj','input.sv','bench.sv']
 e,log=run(cmd,w,'compile',45,bindings);st=execution_state(e,log,'compile')
 if st:return e,log,{'status':st,'stage':'compile'},None
 binary=[str(tools/'usr/bin/vvp'),'simulation.vvp'] if backend=='icarus' else [str(w/'obj/Vcalibration_tb')]
 e,log=run(binary,w,'simulate',3,bindings);return e,log,None,upstream_parser(e,log,w)

def tbgen_jobs():
 id='TBGen/L1/Text/address_mux';src=(u/'data'/id/'address_mux.v').read_text();anchor=re.search(r'assign\s+out\s*=\s*([^;]+);',src);assert anchor
 exprs={'identity':anchor[1],'stuck_zero':"16'h0000",'stuck_ones':"16'hffff",'reversed_select':'select ? in0 : in1','upper_byte_truncation':"{8'b0,(select ? in1[7:0] : in0[7:0])}",'output_xor_1':"(SYNTHESIZED_WIRE_1 | SYNTHESIZED_WIRE_2) ^ 16'h0001",'empty_tb':anchor[1]}
 # Deterministic checker is the existing source-derived reference contract, now
 # reporting the exact requested TEST_PASS / TEST_FAIL terminal marker.
 tb='''`timescale 1ns/1ps
module calibration_tb;reg select;reg[15:0]in0,in1;wire[15:0]out;integer i;integer checks=0;integer failures=0;integer unknowns=0;
address_mux dut(select,in0,in1,out);reg[15:0]expected;
initial begin select=0;in0=0;in1=0;
for(i=0;i<64;i=i+1) begin case(i)
VECTOR_TABLE
endcase expected=select?in1:in0;#2;
if((^out)===1'bx)unknowns=unknowns+1;else begin checks=checks+1;if(out!==expected)failures=failures+1;end end
$display("VALIDITY_CHECKS checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns);
if(failures==0 && unknowns==0)$display("TEST_PASS");else $display("TEST_FAIL");$finish;end endmodule
'''
 rng=random.Random(13579)
 vectors=[(i%2,rng.getrandbits(16),rng.getrandbits(16)) for i in range(64)]
 tb=tb.replace('VECTOR_TABLE','\n'.join(f"{i}:begin select=1'b{v[0]};in0=16'h{v[1]:04x};in1=16'h{v[2]:04x};end" for i,v in enumerate(vectors)))
 (out/'binary_vectors.json').write_text(json.dumps(vectors,indent=2))
 for variant in plan['designs'][id]:
  mutated=src[:anchor.start()]+f'assign out = {exprs[variant]};'+src[anchor.end():]
  used_tb='module calibration_tb;initial $finish;endmodule' if variant=='empty_tb' else tb
  for backend in ['icarus','verilator']:
   yield {'family':'TBGen','design':id,'variant':variant,'backend':backend,'oracle':'64-vector-binary-checker'},src,mutated,used_tb,'checker'

def rtlfix_jobs():
 id='RTLFix/L1/MultiModal/1';raw=(u/'data'/id/'mux.sv').read_text();correct=raw.replace(': ~mux1_out',': mux1_out');assert correct!=raw
 anchor=re.search(r'assign\s+y\s*=\s*([^;]+);',correct);assert anchor
 exprs={'identity':anchor[1],'original_bug':'s1 ? mux2_out : ~mux1_out','stuck_zero':"1'b0",'stuck_one':"1'b1",'reversed_select':'s1 ? mux1_out : mux2_out','all_zero_exception':"(s1 ? mux2_out : mux1_out) ^ ({s1,s0,d0,d1,d2,d3} == 6'b000000)"}
 official=(u/'data'/id/'tb_top.sv').read_text().replace('tb_top','calibration_tb')
 # Only TB top name and waveform output filename are normalized; checking logic unchanged.
 official=official.replace('dump.fst','official_dump.vcd')
 exhaustive='''`timescale 1ns/1ps
module calibration_tb;reg d0,d1,d2,d3,s1,s0;wire y;reg expected;integer i;integer checks=0;integer failures=0;integer unknowns=0;
mux dut(d0,d1,d2,d3,s1,s0,y);
initial begin for(i=0;i<64;i=i+1)begin {s1,s0,d0,d1,d2,d3}=i;expected=s1?(s0?d3:d2):(s0?d1:d0);#2;
if(y===1'bx)unknowns=unknowns+1;else begin checks=checks+1;if(y!==expected)begin failures=failures+1;$display("COUNTEREXAMPLE input=%06b observed=%b expected=%b",i[5:0],y,expected);end end end
$display("VALIDITY_CHECKS checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns);$finish;end endmodule
'''
 for variant in plan['designs'][id]:
  mutated=correct[:anchor.start()]+f'assign y = {exprs[variant]};'+correct[anchor.end():]
  for oracle,tb,kind in [('official_six',official,'official_mux'),('independent_exhaustive',exhaustive,'checker')]:
   for backend in ['icarus','verilator']:yield {'family':'RTLFix','design':id,'variant':variant,'backend':backend,'oracle':oracle},correct,mutated,tb,kind

def sim_trial(job):
 row,original,src,tb,kind=job;w=work('|'.join(str(v) for v in row.values()));row['injection_diff']=diff_write(w,'injection.diff',original,src)
 e,log,failed,parser=simulate(src,tb,row['backend'],w);row.update(decision=failed or outcome(e,log,kind),upstream_generic_parser=parser,simulation_event=e,source_sha256=hashlib.sha256(src.encode()).hexdigest(),bench_sha256=hashlib.sha256(tb.encode()).hexdigest(),role='fixed fault-injection control; not LLM output')
 save(row,w)

def formal_trial(variant,suite,source,property_text,original):
 id='SVAGen/L1/Text/usbh_crc16';row={'family':'SVAGen','design':id,'variant':variant,'backend':'yosys','oracle':suite};w=work('|'.join(row.values()));combined=source.replace('endmodule',property_text+'\nendmodule');(w/'input.sv').write_text(combined);row['injection_diff']=diff_write(w,'injection.diff',original,source);(w/'property.sv').write_text(property_text)
 cmd=[str(tools/'usr/bin/yosys'),'-Q','-T','-p','read_verilog -formal -sv input.sv; prep -top usbh_crc16; flatten; chformal -lower; write_json properties.json; sat -timeout 5 -prove-asserts -verify -show-inputs -show-outputs']
 e,log=run(cmd,w,'formal',15,{'input.sv':digest(w/'input.sv')});st=execution_state(e,log,'formal')
 try:counts=property_counts(w/'properties.json')
 except Exception:counts=None
 if st:decision={'status':st,'raw_proof':'falsified' if 'proof did fail' in log.lower() else 'not_proven'}
 elif counts is None:decision={'status':'error','raw_proof':'missing actual property design'}
 elif counts['assert']==0:decision={'status':'unknown','raw_proof':'vacuous_zero_properties'}
 elif 'SUCCESS!' not in log:decision={'status':'unknown','raw_proof':'no proof completion'}
 else:decision={'status':'pass','raw_proof':'proven'}
 row.update(decision=decision,property_counts=counts,event=e,source_sha256=hashlib.sha256(source.encode()).hexdigest(),property_sha256=hashlib.sha256(property_text.encode()).hexdigest(),scope='combinational binary-input property proof; coverage sensitivity, not independent specification correctness')
 save(row,w)

def formal_jobs():
 id='SVAGen/L1/Text/usbh_crc16';src=(u/'data'/id/'usbh_crc16.v').read_text();single='always @* assert(crc_o[5] == crc_i[13]);'
 matches=list(re.finditer(r'assign\s+(crc_o\[\d+\])\s*=\s*([^;]+);',src));assert len(matches)==16
 full='\n'.join(f"always @* assert({m[1]} == 1'({m[2]}));" for m in matches)
 def replace_lhs(lhs,expr):
  m=next(m for m in matches if m[1]==lhs);return src[:m.start()]+f'assign {lhs} = {expr};'+src[m.end():]
 m15=next(m for m in matches if m[1]=='crc_o[15]')
 variants={'identity':src,'covered_inversion':replace_lhs('crc_o[5]','~crc_i[13]'),'covered_stuck_zero':replace_lhs('crc_o[5]',"1'b0"),'uncovered_inversion':replace_lhs('crc_o[4]','~crc_i[12]'),'operator_error':replace_lhs('crc_o[15]',m15[2].replace('^','|'))}
 for suite,prop in [('single_bit5',single),('all_outputs',full)]:
  for variant in plan['designs'][id]['dut_variants']:yield variant,suite,variants[variant],prop,src
 yield 'constant_identity','constant',src,'always @* assert(1);',src
 yield 'constant_covered_mutant','constant',variants['covered_inversion'],'always @* assert(1);',src
 yield 'empty_identity','empty',src,'',src
 yield 'malformed_identity','malformed',src,'always @* assert(;',src

def ga94_trials():
 id='MGen/L3/Text/GA_94';shared=out/'ga94_shared';shared.mkdir();case=u/'data'/id
 for name in ['dut.v','ref.v']:
  text=(case/name).read_text();(shared/name).write_text(text if '`timescale' in text else '`timescale 1ns/1ps\n'+text)
 raw_tb=(case/'ref_tb.v').read_text();tb=re.sub(r'\$fsdbDump(?:file|vars|MDA|SVA)\s*\([^;()]*\)\s*;','/* diagnostic waveform task omitted */',raw_tb)
 diff_write(shared,'waveform.diff',raw_tb,tb)
 names=ff.extract_verilog_module_names((case/'ref.v').read_text());direct=[n for n in names if re.search(r'\b'+re.escape(n)+r'\s+(\w+)\s*\(',ff._strip_verilog_comments(tb))];assert direct==['CPU_ref'],direct
 reference=ff.parse_verilog_module_interface(re.sub(r'\b(reg|wire|logic)(?=\[)',r'\1 ',(case/'ref.v').read_text()),direct[0]);assert reference
 e,log=run([str(tools/'usr/bin/verilator'),'--cc','--timing','-Wno-fatal','--prefix','RefModel','--top-module',reference.name,'--Mdir','ref_obj','ref.v'],shared,'reference_emit',45)
 if execution_state(e,log,'compile'):raise RuntimeError('GA94 reference emission failed: '+log[-1000:])
 header=(shared/'ref_obj/RefModel.h').read_text();meta={name:int(msb)+1 for name,msb in re.findall(r'VL_(?:IN|OUT)(?:8|16|64|W)?\s*\(\s*&?(\w+)\s*,\s*(\d+)\s*,\s*0(?:\s*,\s*\d+)?\s*\)',header)};assert set(meta)=={p.name for p in reference.ports} and max(meta.values())<=64
 normalized=VerilogModuleInterface(reference.name,[VerilogPort(p.name,p.direction,f'[{meta[p.name]-1}:0]' if meta[p.name]>1 else '') for p in reference.ports],[])
 ev=MGenEvaluator(shared,None,{});(shared/'ref_wrapper.sv').write_text(ev._generate_wrapper(normalized))
 tb=tb.replace('$finish','$display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish')
 pos=tb.rfind('endmodule');tb='import "DPI-C" function void ref_model_release();\n'+tb[:pos]+'final begin ref_model_release(); end\n'+tb[pos:];(shared/'golden_tb.sv').write_text(tb);diff_write(shared,'tb_instrumentation.diff',raw_tb,tb)
 e,log=run(['/usr/bin/make','-C','ref_obj','-f','RefModel.mk','-j1'],shared,'reference_build',45)
 if execution_state(e,log,'compile'):raise RuntimeError('GA94 reference build failed')
 arguments=[];inputs=[];outputs=[]
 for p in reference.ports:
  if p.direction=='input':arguments.append('unsigned long long '+p.name);inputs.append('model.'+p.name+'='+p.name+';')
  else:arguments.append('unsigned long long* '+p.name);outputs.append(p.name)
 prefix='#include "RefModel.h"\n#include <memory>\n#include <cstdio>\n'+CONTEXT_GUARD_CPP+'''struct ReferenceOwner { std::unique_ptr<VerilatedContext> context;std::unique_ptr<RefModel> model;ReferenceOwner():context(new VerilatedContext),model(new RefModel(context.get())){} };
static std::unique_ptr<ReferenceOwner> owner;static unsigned long long validity_calls=0,validity_changes=0;
extern "C" void ref_model_release(){CallerContextGuard guard;if(owner){Verilated::threadContextp(owner->context.get());owner->model->final();owner->model.reset();owner->context.reset();owner.reset();}std::printf("VALIDITY_COUNTS calls=%llu changes=%llu\\n",validity_calls,validity_changes);}
'''
 model_start='extern "C" void ref_model_eval('+','.join(arguments)+'){CallerContextGuard guard;if(!owner)owner.reset(new ReferenceOwner);Verilated::threadContextp(owner->context.get());RefModel& model=*owner->model;'+''.join(inputs)+'model.eval();++validity_calls;'
 mutations={'identity':('value_o_ref','before'),'value_xor_1':('value_o_ref','before ^ 1ULL'),'value_xor_128':('value_o_ref','before ^ 128ULL'),'sign_xor_1':('is_positive_ref','before ^ 1ULL'),'egg_xor_1':('easter_egg_ref','before ^ 1ULL'),'egg_xor_2':('easter_egg_ref','before ^ 2ULL'),'egg_xor_4':('easter_egg_ref','before ^ 4ULL'),'value_zero':('value_o_ref','0ULL'),'value_ones':('value_o_ref','255ULL')}
 def candidate(variant):
  target,expr=mutations.get(variant,mutations['identity']);body=[]
  for name in outputs:
   if name==target:
    mask=(1<<meta[name])-1;body.append('{unsigned long long before=model.'+name+';unsigned long long after=('+expr+') & '+str(mask)+'ULL;if(before!=after)++validity_changes;*'+name+'=after;}')
   else:body.append('*'+name+'=model.'+name+';')
  cpp=prefix+model_start+''.join(body)+'}\n'
  if variant=='malformed_cpp':cpp+='THIS_IS_A_DELIBERATE_FORMAT_ERROR;\n'
  if variant=='nonterminating_cpp':cpp=cpp.replace('model.eval();','for(;;){} model.eval();')
  return cpp
 original=candidate('identity');archive=shared/'ref_obj/libRefModel.a';assert archive.exists()
 for index,variant in enumerate(plan['designs'][id]):
  row={'family':'MGen','design':id,'variant':variant,'backend':'verilator_DPI','oracle':'unchanged_official_CPU_TB'};w=work('|'.join(row.values()));cpp=candidate(variant);(w/'response.cpp').write_text(cpp);row['injection_diff']=diff_write(w,'injection.diff',original,cpp);(shared/'response.cpp').write_text(cpp);bindings={'response.cpp':{'artifact':str((w/'response.cpp').relative_to(out)),'sha256':digest(w/'response.cpp')}}
  if index==0:cmd=[str(tools/'usr/bin/verilator'),'--binary','--timing','-Wno-fatal','--top-module','tb','--Mdir','obj','-CFLAGS','-I'+str(shared/'ref_obj'),'-LDFLAGS',str(archive),'dut.v','ref_wrapper.sv','golden_tb.sv',str(shared/'response.cpp')]
  else:
   (shared/'obj/response.o').unlink(missing_ok=True);cmd=['/usr/bin/make','-C','obj','-f','Vtb.mk','-j1']
  e,log=run(cmd,shared,'candidate_compile',45,bindings);st=execution_state(e,log,'compile')
  if st:
   row.update(decision={'status':st,'stage':'compile'},activation=None,compile_event=e,role='fixed reference-response mutation; not model output');save(row,w);continue
  binary=shared/'obj/Vtb';e,log=run([str(binary)],shared,'candidate_simulate',3,dict(bindings,binary_sha256=digest(binary)))
  row['decision']=mgen_score(e,log);witness=re.search(r'VALIDITY_COUNTS calls=(\d+) changes=(\d+)',log)
  row.update(activation={'calls':int(witness[1]),'changed_calls':int(witness[2])} if witness else None,simulation_event=e,source_sha256=digest(w/'response.cpp'),upstream_generic_parser=upstream_parser(e,log,w),role='fixed reference-response mutation; not LLM output');save(row,w)

if a.tb_only:
 for job in tbgen_jobs():sim_trial(job)
 (out/'results.json').write_text(json.dumps({'results':results,'supervised_command_attempts':len(events),'wall_seconds':time.monotonic()-started,'reason':'compatibility repair: explicit same input table replaces backend-specific $random sequence'},indent=2))
 raise SystemExit(0)
isolation_probes()
# One sequential DPI worker avoids stale/mixed shared artifacts; the other worker
# executes independent simulation/formal jobs. Never more than two processes at once.
other_jobs=list(tbgen_jobs())+list(rtlfix_jobs());f_jobs=list(formal_jobs());assert len(other_jobs)==38 and len(f_jobs)==14
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 ga=pool.submit(ga94_trials)
 for job in other_jobs:sim_trial(job)
 for job in f_jobs:formal_trial(*job)
 ga.result()
summary={'round':plan['round'],'preregistration_plan_sha256':planhash,'upstream_commit':pin,'planned_primary_trials':plan['primary_trials'],'completed_primary_trials':len(results),'supervised_command_attempts':len(events),'wall_seconds':round(time.monotonic()-started,3),'model_api_calls':0,'global_false_positive_rate_claim':False,'results':sorted(results,key=lambda r:(r['family'],r['variant'],str(r.get('oracle')),str(r.get('backend'))))}
(out/'results.json').write_text(json.dumps(summary,indent=2));assert len(results)==63,(len(results),63);print(json.dumps({k:v for k,v in summary.items() if k!='results'}),flush=True)
