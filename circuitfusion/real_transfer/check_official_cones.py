"""Syntax/width diagnostics for released cones; no commercial library assumed."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent;assets=Path(sys.argv[1]);tool=os.environ['CIRCUITFUSION_YOSYS'];out=[]
for path in sorted(assets.glob('*.v')):
    if path.stem=='spi':continue
    p=subprocess.run([tool,'-T','-p',f'read_verilog {path}; hierarchy -top coi; proc; opt_clean; check'],capture_output=True,text=True,env={**os.environ,'YOWASP_CACHE_DIR':os.environ['CIRCUITFUSION_CACHE']},timeout=120)
    lines=(p.stdout+p.stderr).splitlines();warnings=[x.strip() for x in lines if 'Warning:' in x or 'ERROR:' in x]
    warnings=[x.replace(str(assets),'OFFICIAL_CONE_ROOT') for x in warnings]
    out.append({'sample_id':path.stem,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'exit_code':p.returncode,'diagnostics':warnings,'out_of_bounds':any('out of bounds' in x for x in warnings)})
(root/'official_cone_diagnostics.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
