"""Yosys SAT checks the emitted Verilog against a separately emitted reference."""
import json,subprocess,time,os
from pathlib import Path
root=Path(__file__).resolve().parents[1];os.chdir(root);results=[]
for r in json.loads(Path('results/pilot_candidates.json').read_text()):
 w=r['width'];cs=r['constants'];ident=r['id'];src=Path('results/rtl')/f'{ident}.v';m=src.read_text().replace('module top(','module dut(')
 m+=f'module miter(input [{w-1}:0] x, output bad);\n'
 for i,c in enumerate(cs):m+=f'wire [{w-1}:0] y{i}; wire [{w-1}:0] ref{i} = x * {w}\'d{c};\n'
 m+='dut d(.x(x),'+','.join(f'.y{i}(y{i})' for i in range(len(cs)))+');\nassign bad = '+ ' | '.join(f'(|(y{i} ^ ref{i}))' for i in range(len(cs)))+';\nendmodule\n'
 f=Path('results/rtl')/f'{ident}_miter.v';f.write_text(m)
 t=time.perf_counter();p=subprocess.run([str(root/'.venv/bin/yowasp-yosys'),'-Q','-T','-p',f'read_verilog {f}; prep -top miter; flatten; sat -verify -prove bad 0 -show x'],capture_output=True,text=True,timeout=60,env={**os.environ,'XDG_CACHE_HOME':str(root/'.cache')})
 log=p.stdout+p.stderr;Path(f'logs/{ident}_sat.log').write_text(log);ok=p.returncode==0 and 'SUCCESS!' in log;results.append(dict(id=ident,passed=ok,returncode=p.returncode,seconds=time.perf_counter()-t));assert ok,ident
Path('results/rtl_equivalence.json').write_text(json.dumps(results,indent=2));print(f'{len(results)} / {len(results)} emitted RTL equivalence checks passed')
