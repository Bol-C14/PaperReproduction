"""Acquire public assets once, with immutable provenance and a bounded byte limit."""
import hashlib,json,pathlib,subprocess,time,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
ASSETS=ROOT/'assets';ASSETS.mkdir(exist_ok=True)
rows=json.loads((ROOT/'assets_manifest.json').read_text()) if (ROOT/'assets_manifest.json').exists() else []
def fetch(url,name,limit):
    if any(x['path']=='assets/'+name for x in rows): return
    start=time.time()
    with urllib.request.urlopen(url,timeout=60) as r: data=r.read(limit+1)
    assert len(data)<=limit
    (ASSETS/name).write_bytes(data)
    rows.append(dict(url=url,path='assets/'+name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),seconds=time.time()-start))
    (ROOT/'assets_manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
sha='0fcc4186e344f85167d97c1d67994bef01e89036'
fetch(f'https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/{sha}/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib','nangate45.lib',15000000)
fetch('https://raw.githubusercontent.com/lsils/benchmarks/82d8cc6910419298e713a46644ed59fd3df53038/random_control/int2float.blif','int2float.blif',2000000)
up='b82aef22559c6d8c52eb4feb437ebdd32709360e'
downloads=ROOT.parent/'pilot/downloads';downloads.mkdir(exist_ok=True)
for name in ['aig_dg2','pm_dg2']:
    fetch(f'https://raw.githubusercontent.com/zshi0616/DeepCell/{up}/ckpt/{name}.pth',name+'.pth',10000000)
    (downloads/(name+'.pth')).write_bytes((ASSETS/(name+'.pth')).read_bytes())
fetch('https://api.github.com/repos/zshi0616/DeepCell/git/trees/'+up+'?recursive=1','official_tree.json',1000000)
print(json.dumps(rows,indent=2))
