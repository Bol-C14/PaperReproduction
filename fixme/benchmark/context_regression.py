"""Minimal executed causal test of nested Verilator thread context and $finish."""
import argparse,json,os,pathlib,subprocess,time
from isolation import confine
from mgen_support import CONTEXT_GUARD_CPP,mgen_score
p=argparse.ArgumentParser();p.add_argument('--tools',required=True);p.add_argument('--output',required=True);a=p.parse_args();tools=pathlib.Path(a.tools).resolve();out=pathlib.Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
source='''#include "verilated.h"
#include <cstdio>
'''+CONTEXT_GUARD_CPP+'''
VerilatedContext* innerp;
void unsafe_call(){static VerilatedContext inner;innerp=&inner;Verilated::threadContextp(&inner);}
void safe_call(){CallerContextGuard guard;static VerilatedContext inner;innerp=&inner;Verilated::threadContextp(&inner);}
int main(int argc,char** argv){VerilatedContext caller;bool safe=argc>1; if(safe)safe_call();else unsafe_call();
 bool restored=Verilated::threadContextp()==&caller;
 VL_FINISH_MT("finish_probe.sv",1,"");
 std::printf("restored=%d caller_finish=%d inner_finish=%d\\n",restored,caller.gotFinish(),innerp->gotFinish());
 return safe ? !(restored && caller.gotFinish() && !innerp->gotFinish()) : !(!restored && !caller.gotFinish() && innerp->gotFinish());}
'''
(out/'probe.cpp').write_text(source);events=[]
def run(cmd,name,timeout=30):
 t=time.monotonic();e={'command':cmd,'log':name+'.log','timeout_seconds':timeout}
 try:
  z=subprocess.run(cmd,cwd=out,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout,preexec_fn=confine,env={'PATH':'/usr/bin:/bin','LANG':'C','TMPDIR':str(out)})
  e.update(returncode=z.returncode,status='completed');log=z.stdout
 except subprocess.TimeoutExpired as ex:e.update(returncode=None,status='timeout');log=str(ex)
 (out/e['log']).write_text(log);events.append(e);e['seconds']=round(time.monotonic()-t,3);return e,log
inc=tools/'usr/share/verilator/include';e,log=run(['/usr/bin/g++','-std=c++17','-pthread','-I'+str(inc),'-I'+str(inc/'vltstd'),'probe.cpp',str(inc/'verilated.cpp'),str(inc/'verilated_threads.cpp'),'-o','probe'],'compile',30);assert e['returncode']==0,log
for name,args in [('unsafe',[]),('raii_safe',['safe'])]:
 e,log=run([str(out/'probe'),*args],name,2);assert e['returncode']==0,log
assert 'restored=0 caller_finish=0 inner_finish=1' in (out/'unsafe.log').read_text()
assert 'restored=1 caller_finish=1 inner_finish=0' in (out/'raii_safe.log').read_text()
complete={'status':'completed','returncode':0}
checks={'spaced_positive':mgen_score(complete,'Test case Passed')['status']=='pass','joined_positive':mgen_score(complete,'Testcase Passed')['status']=='pass','joined_failed_overrides':mgen_score(complete,'Testcase Passed\nTestcase Failed\nHARNESS_COUNTS checks=100 failures=0')['status']=='fail','spaced_failed_overrides':mgen_score(complete,'Test case Failed\nTest case Passed')['status']=='fail','generic_pass_not_evidence':mgen_score(complete,'Passed')['status']=='unknown','zero_checks':mgen_score(complete,'HARNESS_COUNTS checks=0 failures=0')['status']=='unknown','timeout_overrides_success':mgen_score({'status':'timeout','returncode':None},'Testcase Passed')['status']=='unknown','nonzero_overrides_success':mgen_score({'status':'completed','returncode':9},'Testcase Passed')['status']=='error'}
checks['numeric_failure_overrides_success']=mgen_score(complete,'Testcase Passed\nMismatches: 2 in 100 samples\nHARNESS_COUNTS checks=100 failures=0')['status']=='fail'
checks['zero_summary_is_not_failure']=mgen_score(complete,'Testcase Passed\nMismatches: 0 in 100 samples')['status']=='pass'
assert all(checks.values()),checks
(out/'trace.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events));(out/'results.json').write_text(json.dumps({'context_leak_reproduced':True,'raii_restoration_verified':True,'parser_checks':checks,'passed':True},indent=2));print('PASS: actual $finish context leak and RAII repair; 10 exact-parser/status regressions')
