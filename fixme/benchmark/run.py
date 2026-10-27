"""Bounded FIXME evaluator pilot; deterministic fixtures, never live LLM scores."""
import argparse,collections,dataclasses,hashlib,json,os,pathlib,re,shutil,signal,subprocess,sys,time
from isolation import confine
from evaluation import command_state, simulation_score, clean_response, unsupported_sva_reason, property_counts, formal_score
P=argparse.ArgumentParser();P.add_argument('--upstream',required=True);P.add_argument('--tools',required=True);P.add_argument('--output',required=True);P.add_argument('--only-subsets',nargs='+',choices=['SpeCom','MGen','TBGen','SVAGen','RTLFix','RTLFixText']);P.add_argument('--responses',help='JSON override {subset: {variant: response}}; trusted locally reviewed code only');a=P.parse_args()
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
if a.only_subsets: fixtures={k:v for k,v in fixtures.items() if k in a.only_subsets}
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
 e,log=run(cmd,w,'compile');status,reason=command_state(e,log,'compile')
 if status:return dict(status=status,syntax_pass=False if status=='fail' else None,functional_pass=None,official_status=status,reason=reason)
 e,log=run([str(tools/'usr/bin/vvp'),'simv'],w,'simulate',1)
 return dict(simulation_score(e,log,marker),syntax_pass=True)

def prove(source,w,label):
 combined=w/(label+'.sv');combined.write_text(source)
 design=w/(label+'.json')
 cmd=[str(tools/'usr/bin/yosys'),'-Q','-T','-p',f'read_verilog -formal -sv {combined.name}; prep -top usbh_crc16; flatten; chformal -lower; write_json {design.name}; sat -prove-asserts -verify -show-inputs -show-outputs']
 e,log=run(cmd,w,label)
 try:counts=property_counts(design)
 except (OSError,ValueError,KeyError):counts=None
 return e,log,counts
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
    scored=sim(ev._get_compile_files(w),'dut_tb',w,'TEST_PASS checks=64');r.update(scored)
    # Apply the same adequacy probe to every completed syntactically valid TB,
    # independent of the fixture label. Timeouts do not trigger another run.
    if r['syntax_pass'] and r['status'] in ['pass','fail']:
     dut=w/'address_mux.v';dut.write_text(dut.read_text().replace('assign\tout = SYNTHESIZED_WIRE_1 | SYNTHESIZED_WIRE_2;','assign out = 0;'))
     mutant=sim(ev._get_compile_files(w),'dut_tb',w,'TEST_PASS checks=64')
     r['mutation_killed']=mutant['status']=='fail' and any('TEST_FAIL' in f.read_text(errors='replace') for f in sorted(w.glob('*simulate.log'))[-1:])
     r['mutation_status']=mutant['status']
   elif subset=='RTLFix':
    (w/'mux.sv').write_text(response);shutil.copy2(case/'tb_top.sv',w/'tb_top.sv')
    r.update(sim([w/'mux.sv',w/'tb_top.sv'],'tb_top',w,'ALL TESTS PASSED'))
   elif subset=='MGen':
    ev=MGenEvaluator(w,None,{'keep_tmp':True});ev._prepare_work_dir(case,w,response)
    cmd=[str(tools/'usr/bin/verilator'),'--binary','--timing','-Wno-fatal','--top-module',ev._get_top_module(),'-Mdir','obj_dir']+[str(f) for f in ev._get_compile_files(w)]
    e,log=run(cmd,w,'dpi_compile',90);status,reason=command_state(e,log,'compile')
    r['syntax_pass']=False if status=='fail' else (None if status else True)
    if status:r.update(status=status,reason=reason)
    else:
     e,log=run([str(w/'obj_dir'/('V'+ev._get_top_module()))],w,'dpi_simulate',2)
     r.update(simulation_score(e,log,'Test case Passed',expected_checks=100))
   elif subset=='SVAGen':
    source=(case/'usbh_crc16.v').read_text();code=clean_response(response)
    (w/'assertion.txt').write_text(code)
    unsupported=unsupported_sva_reason(code)
    if unsupported:r.update(status='unsupported',reason=unsupported)
    else:
     e,log,counts=prove(source.replace('endmodule',code+'\nendmodule'),w,'formal')
     r['property_counts']=counts
     r['syntax_pass']=False if re.search(r'syntax error|parse error',log,re.I) else (True if counts is not None else None)
     status,reason=command_state(e,log,'formal');killed=None
     if status is None and counts and counts['assert']>0 and 'SUCCESS!' in log:
      # Same source mutation for all response labels. Constant assertions cannot
      # kill it; the selected meaningful output relationship must do so.
      mutant=source.replace('assign crc_o[5] =     crc_i[13];','assign crc_o[5] =     ~crc_i[13];')
      if mutant==source:raise ValueError('pinned CRC mutation anchor missing')
      me,mlog,mcounts=prove(mutant.replace('endmodule',code+'\nendmodule'),w,'formal_mutant')
      mstatus,mreason=command_state(me,mlog,'formal')
      killed=mstatus=='fail' and 'proof did fail' in mlog.lower() and bool(mcounts and mcounts['assert']>0)
      r.update(mutation_killed=killed,mutation_status=mstatus or 'completed',mutation_reason=mreason,mutation_property_counts=mcounts)
      if mstatus in ['unknown','error']:
       r.update(status=mstatus,functional_pass=None,reason='adequacy probe: '+mreason)
     if 'status' not in r:r.update(formal_score(e,log,counts,killed))
     r['proof_scope']='actual nonzero combinational assertions; all 24 binary input bits; selected output mutant adequacy; not full specification or temporal SVA'
   else:raise ValueError(subset)
  except Exception as ex:r.update(status='error',error=str(ex))
  (w/'result.json').write_text(json.dumps(r,indent=2));results.append(r)
# Pure official formal-log parser check: unknown/inconclusive/zero properties must never pass.
fv=FVRunner({});formal_checks={s:fv._classify_formal_log(s) for s in ['# found: 0\n# proven: 0','# found: 2\n# proven: 1','# found: 2\n# proven: 2','# found: 2\n# falsified: 1','unrecognized']}
summary={'model':'fixed-author-fixture-v1','live_llm':False,'cases':len(results),'statuses':dict(collections.Counter(r['status'] for r in results)),'results':results,'formal_parser_checks':formal_checks,'published_aggregate_reproduced':False,'pass_at_5':None,'reason':'deterministic evaluator controls are not independent model samples'}
(out/'results.json').write_text(json.dumps(summary,indent=2));(out/'trace.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2))
