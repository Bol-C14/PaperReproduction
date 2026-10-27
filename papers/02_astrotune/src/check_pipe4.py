import subprocess,os,json
from eda import ROOT,TOOLS
out=ROOT/'work/pipe4_semantics';out.mkdir(exist_ok=True,parents=True)
env=dict(os.environ,VERILATOR_ROOT=str(TOOLS/'build/share/verilator'),LD_LIBRARY_PATH=str(TOOLS/'deps')+':'+str(TOOLS/'build/lib'))
cmd=[str(TOOLS/'build/bin/verilator'),'--binary','--timing','-CFLAGS','-std=c++20','-Wno-fatal','--top-module','pipe4_semantics','--Mdir',str(out/'obj'),'-j','1',str(ROOT/'benchmarks/multi_pipe_4bit/verified_multi_pipe_4bit.v'),str(ROOT/'tests/pipe4_semantics.v')]
r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=120);(out/'compile.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
r=subprocess.run([str(out/'obj/Vpipe4_semantics')],env=env,capture_output=True,text=True,timeout=20);(out/'simulation.log').write_text(r.stdout+r.stderr)
(ROOT/'results/pipe4_semantics.json').write_text(json.dumps({'command':cmd,'exit':r.returncode,'output':r.stdout,'passed':r.returncode==0 and 'PASS:' in r.stdout},indent=2));print(r.stdout)
