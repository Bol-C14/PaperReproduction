"""Real Icarus positive/negative smoke, no model and no credentials.
Safe refusal if Icarus absent. Does not execute model-generated source.
"""
import hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent

def main():
 tools={n:shutil.which(n) for n in ('iverilog','vvp')}
 if not all(tools.values()):
  print(json.dumps({'status':'NOT_RUN','reason':'iverilog/vvp missing','real_verifier_executions':0}));return 2
 outcomes={}
 original=(P/'upstream/adder.sv').read_text()
 assert original.count('assign X = A + B;')==1
 for control,source in [('positive',original),('negative',original.replace('assign X = A + B;','assign X = A | B;'))]:
  with tempfile.TemporaryDirectory(prefix='t2s-real-rtl-') as tmp:
   d=Path(tmp);(d/'adder.sv').write_text(source);(d/'tb.sv').write_bytes((P/'tb.sv').read_bytes())
   env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':tmp,'TMPDIR':tmp,'LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
   build=subprocess.run([tools['iverilog'],'-g2012','-s','tb','-o',str(d/'sim.vvp'),str(d/'adder.sv'),str(d/'tb.sv')],cwd=d,env=env,capture_output=True,timeout=15)
   if build.returncode:raise RuntimeError('smoke compilation failed; not a functional result')
   result=subprocess.run([tools['vvp'],str(d/'sim.vvp')],cwd=d,env=env,capture_output=True,timeout=15)
   outcomes[control]={'exit_code':result.returncode,'source_sha256':hashlib.sha256(source.encode()).hexdigest()}
 assert outcomes['positive']['exit_code']==0 and outcomes['negative']['exit_code']!=0
 print(json.dumps({'status':'REAL_RTL_SMOKE_PASSED','controls':outcomes,'real_verifier_executions':2},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
