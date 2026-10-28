import os,pathlib,subprocess,json,time,hashlib
r=pathlib.Path(os.environ['E4_WORK_ROOT']);o=r/'results/fluxbench/physical-v1';y=r/'tools/verithoughts/yosys041-install/bin/yosys';iv=r/'tools/cvdp/iverilog-install/bin/iverilog';lib=r/'assets/pdagent/dataset/PlaceReasoner-Bench/bp_fe/lib/NangateOpenCellLibrary_typical.lib';src=r/'assets/fluxbench/picorv32.v';runs=[]
assert (o/'route.odb').is_file() and (o/'route.v').is_file()
cmds=[('route-cell-models',[y,'-p',f'read_liberty -ignore_miss_func {lib}; read_verilog route.v; rename picorv32 impl; hierarchy -check -top impl; proc; opt_clean; write_verilog -noattr combined-route.v']),('compile-route',[iv,'-g2012','-s','tb','-o','route.vvp','tb.v',src,'combined-route.v']),('simulate-route',[iv.with_name('vvp'),'route.vvp'])]
try:
 for name,cmd in cmds:
  t=time.monotonic();p=subprocess.run([str(x) for x in cmd],cwd=o,env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'OMP_NUM_THREADS':'4'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(o/(name+'.log')).write_bytes(p.stdout);runs.append(dict(id=name,command=[str(x) for x in cmd],returncode=p.returncode,seconds=time.monotonic()-t));assert p.returncode==0,name
  if name=='simulate-route':assert b'VERIFIED cycles=1000 fetches=333' in p.stdout
finally:(o/'final-functional-runs.json').write_text(json.dumps(runs,indent=2)+'\n')
