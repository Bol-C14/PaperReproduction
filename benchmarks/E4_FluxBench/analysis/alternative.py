import hashlib,json,os,pathlib,subprocess,time
r=pathlib.Path(os.environ['E4_WORK_ROOT']); out=r/'results/fluxbench/port-v1'; y=r/'tools/verithoughts/yosys041-install/bin/yosys'; iv=r/'tools/cvdp/iverilog-install/bin/iverilog'; src=r/'assets/fluxbench/picorv32.v'
assert not (out/'alternative2-summary.json').exists()
runs=[]
env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','LANG','TMPDIR']};env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
for name,args in [
 ('synth-alternative2',[y,'-p',f'read_verilog {src}; synth -top picorv32 -noabc -noalumacc; check -assert; rename picorv32 impl; write_verilog alternative2.v; write_json alternative2.json']),
 ('reload-alternative2',[y,'-p','read_verilog alternative2.v; hierarchy -check -top impl; proc; check -assert; stat']),
 ('compile-alternative2',[iv,'-g2012','-s','tb','-o','alternative2.vvp','tb.v',src,'alternative2.v']),
 ('simulate-alternative2',[iv.with_name('vvp'),'alternative2.vvp'])]:
 t=time.monotonic();p=subprocess.run([str(x) for x in args],cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/(name+'.log')).write_bytes(p.stdout);runs.append(dict(id=name,command=[str(x) for x in args],seconds=time.monotonic()-t,exit_code=p.returncode));assert p.returncode==0
assert b'VERIFIED cycles=1000 fetches=333' in p.stdout
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(out/'alternative2.v')!=h(out/'mapped.v')
d=json.load(open(out/'alternative2.json'))['modules']['impl'];assert d['cells']
(out/'alternative2-summary.json').write_text(json.dumps(dict(status='reference_calibration',reason='ABC/noABC identical in this build; noalumacc changes actual netlist',runs=runs,netlist_sha256=h(out/'alternative2.v'),database_sha256=h(out/'alternative2.json'),cells=len(d['cells']),cycles=1000,fetches=333),indent=2)+'\n')
