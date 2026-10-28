import os,pathlib,subprocess,time,json,hashlib
r=pathlib.Path(os.environ['E4_WORK_ROOT']);o=r/'results/fluxbench/physical-v1';y=r/'tools/verithoughts/yosys041-install/bin/yosys';abc=r/'tools/abc-rl/abc/abc';lib=r/'assets/pdagent/dataset/PlaceReasoner-Bench/bp_fe/lib/NangateOpenCellLibrary_typical.lib';src=r/'assets/fluxbench/picorv32.v'
env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4'};runs=[]
commands=[('unmap',[y,'-p',f'read_verilog {src}; synth -top picorv32 -noabc; dffunmap; write_blif unmapped.blif']),('abc-map',[abc,'-c',f'read_lib {lib}; read_blif unmapped.blif; strash; map; write_verilog abc.v']),('dffmap',[y,'-p',f'read_verilog abc.v; hierarchy -top picorv32; proc; dfflibmap -liberty {lib}; clean; read_liberty -lib {lib}; hierarchy -check -top picorv32; check -assert; stat; write_verilog -noattr mapped.v; write_json mapped.json'])]
try:
 for name,cmd in commands:
  t=time.monotonic();p=subprocess.run([str(x) for x in cmd],cwd=o,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(o/(name+'.log')).write_bytes(p.stdout);runs.append(dict(id=name,command=[str(x) for x in cmd],returncode=p.returncode,seconds=time.monotonic()-t));assert p.returncode==0,name
finally:
 (o/'mapping-runs.json').write_text(json.dumps(runs,indent=2)+'\n')
