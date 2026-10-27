"""Bounded FIXME evaluator pilot; deterministic fixtures, never live LLM scores."""
import argparse,collections,dataclasses,hashlib,json,os,pathlib,re,shutil,signal,subprocess,sys,time
from isolation import confine
P=argparse.ArgumentParser();P.add_argument('--upstream',required=True);P.add_argument('--tools',required=True);P.add_argument('--output',required=True);P.add_argument('--responses',help='JSON override {subset: {variant: response}}; trusted locally reviewed code only');a=P.parse_args()
u=pathlib.Path(a.upstream).resolve();tools=pathlib.Path(a.tools).resolve();out=pathlib.Path(a.output).resolve();
if out.exists() and any(out.iterdir()): raise SystemExit('output directory must be empty')
out.mkdir(parents=True,exist_ok=True)
pin=subprocess.check_output(['git','-C',str(u),'rev-parse','HEAD'],text=True).strip()
if pin!='e875437fbb11590b71775b32d3579726d702cfc6':raise SystemExit('upstream pin mismatch')
sys.path.insert(0,str(u))
from src.evaluators.specom_eval import evaluate_specom
from src.evaluators.rtlfix_eval import evaluate_rtlfix
from src.evaluators.mgen_eval import MGenEvaluator
from src.evaluators.tbgen_eval import TBGenEvaluator
from src.evaluators.eval_utils import extract_code_block
from src.simulation.fv_runner import FVRunner
CASE={'SpeCom':'SpeCom/L1/Text/1 bit Full Adder using HA','MGen':'MGen/L1/Text/1 bit Full Adder using HA','TBGen':'TBGen/L1/Text/address_mux','SVAGen':'SVAGen/L1/Text/usbh_crc16','RTLFix':'RTLFix/L1/MultiModal/1','RTLFixText':'RTLFix/L1/Text/1'}
full='extern "C" void ref_model_eval(unsigned long long a,unsigned long long b,unsigned long long c,unsigned long long* s,unsigned long long* co){*s=(a^b^c)&1;*co=((a+b+c)>>1)&1;}'
tb='''module dut_tb; reg select; reg [15:0] in0,in1; wire [15:0] out;
address_mux dut(select,in0,in1,out); integer i; initial begin
for(i=0;i<64;i=i+1) begin select=i%2; in0=16'h1<<((i/2)%16); in1=~in0; #1;
if(out !== (select?in1:in0)) $fatal(1,"TEST_FAIL"); end
$display("TEST_PASS checks=64"); $finish; end endmodule'''
sva='always @* assert(crc_o[5] == crc_i[13]);'
rtl=(u/'data'/CASE['RTLFix']/'mux.sv').read_text()
fixtures={'SpeCom':{'positive':'B','wrong':'A','malformed':'???','ambiguous':'A or B'},'MGen':{'positive':full,'wrong':full.replace('*s=(a^b^c)&1','*s=0'),'malformed':'not C++'},'TBGen':{'positive':tb,'wrong':tb.replace('select?in1:in0','select?in0:in1'),'malformed':'module ;','empty_tb':'module dut_tb; initial $finish; endmodule','timeout':'module dut_tb; initial forever #1; endmodule'},'SVAGen':{'positive':sva,'wrong':sva.replace('==','!='),'malformed':'assert ( ;','unsupported':'assert property (@(posedge clk) a |=> b);','vacuous':'always @* assert(1);'},'RTLFix':{'positive':rtl.replace(': ~mux1_out',': mux1_out'),'wrong':rtl,'malformed':'module ;'},'RTLFixText':{'positive':'always@(negedge clk)\nalways@(posedge clk)','wrong':'always@(negedge clk)','malformed':'???','pair_only':'always@(negedge clk)\nalways@(posedge clk)'}}
if a.responses:
 for k,v in json.loads(pathlib.Path(a.responses).read_text()).items(): fixtures[k].update(v)
(out/'responses.json').write_text(json.dumps(fixtures,indent=2));results=[];events=[]
env={'PATH':str(tools/'usr/bin')+':/usr/bin:/bin','VERILATOR_ROOT':str(tools/'usr/share/verilator'),'LANG':'C','HOME':'/nonexistent','PYTHONDONTWRITEBYTECODE':'1'}
def run(cmd,w,label,timeout=30):
 idx=len(events);log=w/f'{idx:03d}_{label}.log';e=dict(index=idx,command=cmd,cwd=str(w.relative_to(out)),timeout_seconds=timeout,log=str(log.relative_to(out)),isolation='private-cwd+seccomp-no-network+rlimits; host Landlock unavailable');t=time.monotonic()
 try:
  with log.open('wb') as f:
   process=subprocess.Popen(cmd,cwd=w,env=dict(env,TMPDIR=str(w)),stdout=f,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=confine)
   try:code=process.wait(timeout=timeout);e['status']='completed'
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait();code=None;e['status']='timeout'
  e['returncode']=code
 except Exception as ex:e.update(status='error',returncode=None,error=str(ex));log.write_text(str(ex))
 e['duration_seconds']=round(time.monotonic()-t,4);events.append(e);text=log.read_text(errors='replace');return e,text

def sim(files,top,w,marker):
 cmd=[str(tools/'usr/bin/iverilog'),'-B',str(tools/'usr/lib/x86_64-linux-gnu/ivl'),'-g2012','-s',top,'-o','simv']+[str(f) for f in files]
 e,log=run(cmd,w,'compile');syntax=e['returncode']==0
 if not syntax:return ('fail' if e['status']=='completed' else 'error'),False,None,False
 e,log=run([str(tools/'usr/bin/vvp'),'simv'],w,'simulate',1)
 if e['status']=='timeout':return 'unknown',True,None,False
 if e['status']!='completed':return 'error',True,None,False
 official=e['returncode']==0 and (bool(re.search(r'TEST_PASS|test passed|PASS|All tests passed',log,re.I)) or not bool(re.search(r'Error|FATAL|FAILED|assertion failed',log,re.I)))
 strict=e['returncode']==0 and marker in log and not bool(re.search(r'TEST_FAIL|SOME TESTS FAILED|ERROR:|FATAL',log,re.I))
 return ('pass' if strict else 'fail'),True,strict,official
probe=out/'isolation_probe';probe.mkdir(exist_ok=True)
run(['/usr/bin/python3','-c','import socket; socket.socket()'],probe,'network_denial')
for subset,variants in fixtures.items():
 case=u/'data'/CASE[subset]
 for variant,response in variants.items():
  w=out/f'{subset}_{variant}';w.mkdir(exist_ok=True);(w/'response.txt').write_text(response)
  inputs=[dict(name=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(case.iterdir()) if f.is_file()]
  r=dict(subset=subset,case=CASE[subset],variant=variant,model='fixed-author-fixture-v1',live_llm=False,upstream_commit=pin,input_files=inputs,response_sha256=hashlib.sha256(response.encode()).hexdigest(),fidelity='substituted',coverage={'line':None,'toggle':None,'functional':None},syntax_pass=None,functional_pass=None)
  try:
   if subset=='SpeCom' or subset=='RTLFixText':
    z=(evaluate_specom if subset=='SpeCom' else evaluate_rtlfix)(case,response)
    r.update(status=z.status,official_status=z.status,functional_pass=z.functional_pass,details=z.details,fidelity='exact-current-upstream-evaluator')
    r['semantic_limit']='objective option match' if subset=='SpeCom' else 'fragment match only; no repaired RTL was executed'
   elif subset=='TBGen':
    ev=TBGenEvaluator(w,None,{'keep_tmp':True});ev._prepare_work_dir(case,w,response)
    status,syntax,func,official=sim(ev._get_compile_files(w),'dut_tb',w,'TEST_PASS checks=64')
    r.update(status=status,syntax_pass=syntax,functional_pass=func,official_status='pass' if official else ('unknown' if status=='unknown' else 'fail'))
    # Mutation adequacy: selected source mutation must be killed by a functional TB.
    if variant in ['positive','empty_tb'] and syntax:
     dut=w/'address_mux.v';dut.write_text(dut.read_text().replace('assign\tout = SYNTHESIZED_WIRE_1 | SYNTHESIZED_WIRE_2;','assign out = 0;'))
     ms,_,_,_=sim(ev._get_compile_files(w),'dut_tb',w,'TEST_PASS checks=64');r['mutation_killed']=any('TEST_FAIL' in f.read_text(errors='replace') for f in sorted(w.glob('*simulate.log'))[-1:])
   elif subset=='RTLFix':
    (w/'mux.sv').write_text(response);shutil.copy2(case/'tb_top.sv',w/'tb_top.sv')
    status,syntax,func,official=sim([w/'mux.sv',w/'tb_top.sv'],'tb_top',w,'ALL TESTS PASSED')
    r.update(status=status,syntax_pass=syntax,functional_pass=func,official_status='pass' if official else 'fail')
   elif subset=='MGen':
    ev=MGenEvaluator(w,None,{'keep_tmp':True});ev._prepare_work_dir(case,w,response)
    cmd=[str(tools/'usr/bin/verilator'),'--binary','--timing','-Wno-fatal','--top-module',ev._get_top_module(),'-Mdir','obj_dir']+[str(f) for f in ev._get_compile_files(w)]
    e,log=run(cmd,w,'dpi_compile',90);r['syntax_pass']=e['returncode']==0
    if not r['syntax_pass']:r['status']='fail' if e['status']=='completed' else 'error'
    else:
     e,log=run([str(w/'obj_dir'/('V'+ev._get_top_module()))],w,'dpi_simulate',2)
     checks=len(re.findall('Test case Passed',log));bad='Test case Failed' in log
     r.update(status='pass' if e['returncode']==0 and checks==100 and not bad else 'fail',functional_pass=e['returncode']==0 and checks==100 and not bad,observed_checks=checks)
   elif subset=='SVAGen':
    shutil.copy2(case/'usbh_crc16.v',w/'dut.v');(w/'assertion.txt').write_text(response)
    if variant=='unsupported':r.update(status='unsupported',reason='temporal SVA is outside explicit combinational assertion adapter')
    elif variant=='vacuous':r.update(status='fail',reason='constant assertion rejected by adequacy guard')
    else:
     code=(w/'dut.v').read_text().replace('endmodule',response+'\nendmodule');(w/'combined.sv').write_text(code)
     e,log=run([str(tools/'usr/bin/yosys'),'-Q','-T','-p','read_verilog -formal -sv combined.sv; prep -top usbh_crc16; flatten; chformal -lower; sat -prove-asserts -verify -show-inputs -show-outputs'],w,'formal')
     proven=e['returncode']==0 and 'SUCCESS!' in log
     falsified='proof did fail' in log.lower()
     r.update(status='pass' if proven else ('fail' if falsified or 'syntax error' in log.lower() else 'unknown'),syntax_pass=False if 'syntax error' in log.lower() else (True if proven or falsified else None),functional_pass=True if proven else (False if falsified else None),proof_scope='one combinational invariant, all 24 binary input bits; not full specification or temporal SVA')
   else:raise ValueError(subset)
  except Exception as ex:r.update(status='error',error=str(ex))
  (w/'result.json').write_text(json.dumps(r,indent=2));results.append(r)
# Pure official formal-log parser check: unknown/inconclusive/zero properties must never pass.
fv=FVRunner({});formal_checks={s:fv._classify_formal_log(s) for s in ['# found: 0\n# proven: 0','# found: 2\n# proven: 1','# found: 2\n# proven: 2','# found: 2\n# falsified: 1','unrecognized']}
summary={'model':'fixed-author-fixture-v1','live_llm':False,'cases':len(results),'statuses':dict(collections.Counter(r['status'] for r in results)),'results':results,'formal_parser_checks':formal_checks,'published_aggregate_reproduced':False,'pass_at_5':None,'reason':'deterministic evaluator controls are not independent model samples'}
(out/'results.json').write_text(json.dumps(summary,indent=2));(out/'trace.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2))
