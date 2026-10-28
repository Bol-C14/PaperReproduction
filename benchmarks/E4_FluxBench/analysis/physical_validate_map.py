import os,pathlib,subprocess,json,time
r=pathlib.Path(os.environ['E4_WORK_ROOT']);o=r/'results/fluxbench/physical-v1';y=r/'tools/verithoughts/yosys041-install/bin/yosys';iv=r/'tools/cvdp/iverilog-install/bin/iverilog';lib=r/'assets/pdagent/dataset/PlaceReasoner-Bench/bp_fe/lib/NangateOpenCellLibrary_typical.lib';src=r/'assets/fluxbench/picorv32.v';runs=[]
(o/'tb.v').write_bytes((o/'../port-v1/tb.v').read_bytes())
cmds=[('cell-models-recovery',[y,'-p',f'read_liberty -ignore_miss_func {lib}; read_verilog simulation.v; hierarchy -check -top impl; write_verilog -noattr combined.v']),('compile-technology',[iv,'-g2012','-s','tb','-o','technology.vvp','tb.v',src,'combined.v']),('simulate-technology',[iv.with_name('vvp'),'technology.vvp']),('tie-mapping',[y,'-p',f'read_verilog technology.v; hierarchy -top picorv32; hilomap -hicell LOGIC1_X1 Z -locell LOGIC0_X1 Z; read_liberty -lib {lib}; hierarchy -check -top picorv32; check -assert; write_verilog -noattr physical.v; write_json physical.json'])]
try:
 for name,cmd in cmds:
  t=time.monotonic();p=subprocess.run([str(x) for x in cmd],cwd=o,env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'OMP_NUM_THREADS':'4'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(o/(name+'.log')).write_bytes(p.stdout);runs.append(dict(id=name,command=[str(x) for x in cmd],returncode=p.returncode,seconds=time.monotonic()-t));assert p.returncode==0,name
  if name=='simulate-technology':assert b'VERIFIED cycles=1000 fetches=333' in p.stdout
finally:(o/'validate-mapping-runs.json').write_text(json.dumps(runs,indent=2)+'\n')
