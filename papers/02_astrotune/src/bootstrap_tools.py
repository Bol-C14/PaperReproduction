"""Fetch verified public OpenLane tool layers without Docker's VFS layer duplication.
No root, credentials, external scripts, containers, or global cleanup required.
"""
import urllib.request,json,hashlib,tarfile,shutil,os
from pathlib import Path
WORK=Path(os.environ.get('ASTROTUNE_SETUP','/workspace/scratch/astrotune'));WORK.mkdir(parents=True,exist_ok=True)
REPO='efabless/openlane';MANIFEST='sha256:8d74595b533c5f09aaf46ad74d3d8bb5b8300e9b5932db4f7d17b20a6651a1ab'
token=json.load(urllib.request.urlopen('https://auth.docker.io/token?service=registry.docker.io&scope=repository:'+REPO+':pull'))['token']
def fetch(kind,digest,path):
 if path.exists() and 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()==digest:return
 req=urllib.request.Request('https://registry-1.docker.io/v2/'+REPO+'/'+kind+'/'+digest,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.docker.distribution.manifest.v2+json'})
 with urllib.request.urlopen(req,timeout=180) as r,path.open('wb') as f:shutil.copyfileobj(r,f)
 assert 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()==digest,path
p=WORK/'manifest.raw.json';fetch('manifests',MANIFEST,p);manifest=json.loads(p.read_text());tools=WORK/'tools';tools.mkdir(exist_ok=True)
prefixes=['libtcl8.5','libtclreadline','libpython3.6m','libreadline.so.6','libffi.so.6','libtinfo.so.5','libncurses.so.5']
for i in (0,3,21,22,24):
 layer=manifest['layers'][i];p=WORK/f'layer{i}.tgz';fetch('blobs',layer['digest'],p)
 with tarfile.open(p) as t:
  if i in (21,22,24):t.extractall(tools,filter='data')
  else:
   for m in t:
    if not m.isfile():continue
    if any(Path(m.name).name.startswith(x) for x in prefixes):
     dest=tools/'deps'/Path(m.name).name;dest.parent.mkdir(exist_ok=True)
     with t.extractfile(m) as f,dest.open('wb') as o:shutil.copyfileobj(f,o)
    if '/tcl8.5/' in m.name or '/tclreadline' in m.name:t.extract(m,tools/'runtime',filter='data')
for p in list((tools/'deps').iterdir()):
 for pre in prefixes:
  link=tools/'deps'/pre
  if p.name.startswith(pre) and p.name!=pre and not link.exists():link.symlink_to(p.name)
link=tools/'build/share/verilator/bin/verilator_bin'
if not link.exists():link.symlink_to('../../../bin/verilator_bin')
p=tools/'build/share/verilator/include/verilated.mk';p.write_text(p.read_text().replace('/opt/rh/devtoolset-8/root/usr/bin/g++','/usr/bin/g++').replace('-mno-cet',''))
# Platform public source is pinned separately. Preserve all embedded license notices.
provenance=json.loads((Path(__file__).resolve().parents[1]/'evidence/platform_provenance.json').read_text());commit=provenance['commit'];platform=WORK/'platform';platform.mkdir(exist_ok=True)
files={'cells.lib':'lib/NangateOpenCellLibrary_typical.lib','tech.lef':'lef/NangateOpenCellLibrary.tech.lef','cells.lef':'lef/NangateOpenCellLibrary.macro.lef','setRC.tcl':'setRC.tcl'}
for dest,src in files.items():
 p=platform/dest
 if not p.exists():
  url='https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/'+commit+'/flow/platforms/nangate45/'+src
  with urllib.request.urlopen(url,timeout=120) as r,p.open('wb') as f:shutil.copyfileobj(r,f)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==provenance['platform_sha256'][dest],dest
print('Verified tools:',tools,'Platform:',platform)
