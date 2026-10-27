"""Bounded evaluator reliability regressions, independent of fixture names.

Reuses selected existing fixtures with overrides. Infrastructure probes execute
small local Python commands; those are evaluator tests, never hardware scores.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from evaluation import command_state, simulation_score, formal_score
from isolation import confine

p=argparse.ArgumentParser();p.add_argument('--upstream',required=True);p.add_argument('--tools',required=True);p.add_argument('--output',required=True);a=p.parse_args()
out=Path(a.output).resolve()
if out.exists() and any(out.iterdir()):raise SystemExit('output must be empty')
out.mkdir(parents=True)
runner=Path(__file__).with_name('run.py');checks=[];events=[]
def check(name,condition):
 checks.append({'name':name,'passed':bool(condition)})
 if not condition:raise AssertionError(name)
def suite(name,subsets,responses,tools=None):
 f=out/(name+'_responses.json');f.write_text(json.dumps(responses,indent=2));dest=out/name
 cmd=[sys.executable,str(runner),'--upstream',str(Path(a.upstream).resolve()),'--tools',str(Path(tools or a.tools).resolve()),'--output',str(dest),'--responses',str(f),'--only-subsets']+subsets
 e,log=execute(cmd,name+'_runner',120,isolated=False)
 check(name+'_runner_completed',e.get('returncode')==0)
 data=json.loads((dest/'results.json').read_text());return {(r['subset'],r['variant']):r for r in data['results']}
def execute(cmd,name,timeout=1,isolated=True):
 w=out/(name+'_cwd');w.mkdir();log=out/(name+'.log');t=time.monotonic();e={'command':cmd,'cwd':str(w.relative_to(out)),'log':str(log.relative_to(out)),'timeout_seconds':timeout,'isolation':'seccomp+rlimits' if isolated else 'orchestration; child evaluators isolated'}
 try:
  with log.open('wb') as f:
   proc=subprocess.Popen(cmd,cwd=w,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=confine if isolated else None)
   try:e['returncode']=proc.wait(timeout);e['status']='completed'
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait();e.update(returncode=None,status='timeout')
 except Exception as ex:e.update(returncode=None,status='error',error=str(ex));log.write_text(str(ex))
 e['duration_seconds']=round(time.monotonic()-t,4);events.append(e);return e,log.read_text(errors='replace')

# Replace response bodies under contrary existing labels: no label may determine scoring.
correct='always @* assert(crc_o[5] == crc_i[13]);'
r=suite('response_swap',['SVAGen'],{'SVAGen':{'positive':'wire no_properties;','wrong':correct,'malformed':'always @* assert(1);','unsupported':correct,'vacuous':'assert property (@(posedge clk) a |=> b);'}})
for v,expected in [('positive','unknown'),('wrong','pass'),('malformed','unknown'),('unsupported','pass'),('vacuous','unsupported')]:check('response_content_'+v,r['SVAGen',v]['status']==expected)
check('actual_zero_property_count',r['SVAGen','positive']['property_counts']['assert']==0)
check('constant_cannot_kill_mutant',r['SVAGen','malformed'].get('mutation_killed') is False)
check('nonzero_real_property_count',r['SVAGen','wrong']['property_counts']['assert']>0)

# Actual missing executable through the real adapters, not canned status records.
r=suite('missing_tool',['MGen','TBGen','SVAGen','RTLFix'],{},tools=out/'missing_tools')
for subset in ['MGen','TBGen','SVAGen','RTLFix']:
 for variant in ['positive','wrong','malformed']:check('missing_tool_'+subset+'_'+variant,r[subset,variant]['status']=='error')

# Real C++ DPI timeout, crash and valid response under contrary names.
full='extern "C" void ref_model_eval(unsigned long long a,unsigned long long b,unsigned long long c,unsigned long long* s,unsigned long long* co){*s=(a^b^c)&1;*co=((a+b+c)>>1)&1;}'
r=suite('dpi_execution',['MGen'],{'MGen':{'positive':full.replace('*s=', 'for(;;){} *s='),'wrong':full.replace('*s=', '__builtin_trap(); *s='),'malformed':full}})
check('dpi_timeout_unknown',r['MGen','positive']['status']=='unknown' and r['MGen','positive']['functional_pass'] is None)
check('dpi_crash_error',r['MGen','wrong']['status']=='error' and r['MGen','wrong']['functional_pass'] is None)
check('dpi_valid_under_malformed_label',r['MGen','malformed']['status']=='pass')

# Execute bounded process outcomes, route their actual state through the shared
# compile/simulation/formal classifier, and check returncode precedence.
probes=[('timeout',['/usr/bin/python3','-c','while True: pass'],.1,'unknown'),('missing',[str(out/'no-executable')],1,'error'),('crash',['/usr/bin/python3','-c','import os,signal; os.kill(os.getpid(),signal.SIGSEGV)'],1,'error'),('unrecognized_exit',['/usr/bin/python3','-c','raise SystemExit(9)'],1,'error'),('missing_dependency',['/usr/bin/python3','-c','print("command not found"); raise SystemExit(127)'],1,'error')]
for name,cmd,timeout,expected in probes:
 e,log=execute(cmd,name,timeout)
 for phase in ['compile','simulation','formal']:check(name+'_'+phase,command_state(e,log,phase)[0]==expected)
e,log=execute(['/usr/bin/python3','-c','print("syntax error");raise SystemExit(1)'],'candidate_syntax')
check('syntax_compile_fail',command_state(e,log,'compile')[0]=='fail')
check('syntax_formal_fail',command_state(e,log,'formal')[0]=='fail')
e,log=execute(['/usr/bin/python3','-c','print("TEST_PASS");raise SystemExit(9)'],'nonzero_success_text')
check('nonzero_cannot_pass_simulation',simulation_score(e,log,'TEST_PASS')['status']=='error')
e,log=execute(['/usr/bin/python3','-c','print("SUCCESS!");raise SystemExit(9)'],'nonzero_proof_text')
check('nonzero_cannot_pass_formal',formal_score(e,log,{'assert':1,'assume':0},True)['status']=='error')
(out/'trace.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
(out/'regression.json').write_text(json.dumps({'kind':'evaluator-regression-not-model-results','checks':checks,'passed':all(c['passed'] for c in checks)},indent=2))
print(f'PASS: {len(checks)} content/property/tool-state regression checks')
