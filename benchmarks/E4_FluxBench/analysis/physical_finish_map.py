import os,pathlib,subprocess,time,json,hashlib
r=pathlib.Path(os.environ['E4_WORK_ROOT']);o=r/'results/fluxbench/physical-v1';y=r/'tools/verithoughts/yosys041-install/bin/yosys';iv=r/'tools/cvdp/iverilog-install/bin/iverilog';lib=r/'assets/pdagent/dataset/PlaceReasoner-Bench/bp_fe/lib/NangateOpenCellLibrary_typical.lib';src=r/'assets/fluxbench/picorv32.v'
env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','LANG']};env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4');runs=[]
def run(name,cmd):
 t=time.monotonic();p=subprocess.run([str(x) for x in cmd],cwd=o,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(o/(name+'.log')).write_bytes(p.stdout);runs.append(dict(id=name,command=[str(x) for x in cmd],returncode=p.returncode,seconds=time.monotonic()-t));assert p.returncode==0,name;return p.stdout
try:
 run('abc-interface',[y,'-p','read_verilog abc.v; proc; write_json abc-interface.json'])
 old=json.load(open(o/'../port-v1/mapped.json'))['modules']['impl']['ports'];ports=json.load(open(o/'abc-interface.json'))['modules']['picorv32']['ports']
 text='module picorv32('+', '.join(old)+');\n'
 for n,p in old.items():text+=p['direction']+' '+('['+str(len(p['bits'])-1)+':0] ' if len(p['bits'])>1 else '')+n+';\n'
 pins=[]
 for n in ports:
  expr='clk' if n=='clock' else n
  assert n=='clock' or n.split('[')[0] in old,n
  pins.append('.\\'+n+' ('+expr+')')
 text+='scalar_core inner(\n'+',\n'.join(pins)+');\nendmodule\n';(o/'wrapper.v').write_text(text)
 run('mapped-interface',[y,'-p',f'read_verilog abc.v; rename picorv32 scalar_core; read_verilog wrapper.v; hierarchy -top picorv32; flatten; proc; dfflibmap -liberty {lib}; clean; read_liberty -lib {lib}; hierarchy -check -top picorv32; check -assert; stat; write_verilog -noattr technology.v; write_json technology.json; rename picorv32 impl; write_verilog -noattr simulation.v'])
 run('cell-models',[y,'-p',f'read_liberty {lib}; write_verilog -noattr cells.v'])
 (o/'tb.v').write_bytes((o/'../port-v1/tb.v').read_bytes())
 run('compile-technology',[iv,'-g2012','-s','tb','-o','technology.vvp','tb.v',src,'simulation.v','cells.v'])
 b=run('simulate-technology',[iv.with_name('vvp'),'technology.vvp']);assert b'VERIFIED cycles=1000 fetches=333' in b
finally:
 (o/'finish-mapping-runs.json').write_text(json.dumps(runs,indent=2)+'\n')
