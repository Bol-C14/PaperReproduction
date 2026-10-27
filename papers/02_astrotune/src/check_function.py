"""Execute upstream testbenches after changing ONLY expected DUT module names."""
import json,re,os,subprocess,sys
from pathlib import Path
from eda import ROOT,TOOLS
m=json.loads((ROOT/'benchmarks/manifest.json').read_text())['designs'];results=[]
env=dict(os.environ,VERILATOR_ROOT=str(TOOLS/'build/share/verilator'),LD_LIBRARY_PATH=str(TOOLS/'deps')+':'+str(TOOLS/'build/lib'))
for d in m:
 if len(sys.argv)>1 and d['id'] not in sys.argv[1:]:continue
 out=ROOT/'work/function'/d['id'];out.mkdir(parents=True,exist_ok=True)
 tb=(ROOT/d['rtl']).parent/'testbench.v';text=tb.read_text();text=re.sub(r'\b'+re.escape(d['id'])+r'\b',d['top'],text);(out/'tb.v').write_text(text)
 top=re.search(r'\bmodule\s+(\w+)',text)[1]
 cmd=[str(TOOLS/'build/bin/verilator'),'--binary','--timing','-CFLAGS','-std=c++20','-Wno-fatal','--top-module',top,'--Mdir',str(out/'obj'),'-j','1',str(ROOT/d['rtl']),str(out/'tb.v')]
 r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=120);(out/'compile.log').write_text(r.stdout+r.stderr)
 row={'design':d['id'],'command':cmd,'compile_exit':r.returncode,'adaptation':'DUT module-name substitution only; upstream testbench retained'}
 if r.returncode==0:
  try:
   r=subprocess.run([str(out/'obj'/('V'+top))],env=env,capture_output=True,text=True,timeout=15);(out/'simulation.log').write_text(r.stdout+r.stderr);row.update(sim_exit=r.returncode,passed=('Passed' in r.stdout and 'failures' not in r.stdout.lower()),output=r.stdout)
  except subprocess.TimeoutExpired as e:
   text=(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else (e.stdout or '');(out/'simulation.log').write_text(text);row.update(timeout=True,passed=False,output=text)
 else:row['passed']=False
 results.append(row);print(d['id'],row['passed'],row.get('output',r.stderr[-400:]),flush=True)
 (ROOT/'results'/('function_checks_stress.json' if len(sys.argv)>1 else 'function_checks.json')).write_text(json.dumps(results,indent=2))
