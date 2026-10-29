"""Anonymous OCI manifest-only inspection; never downloads image layers."""
import urllib.request,json,hashlib
from pathlib import Path
out=Path('oci');out.mkdir(exist_ok=True)
repo='scaleapi/swe-bench_pro-v2'
token=json.load(urllib.request.urlopen('https://ghcr.io/token?service=ghcr.io&scope=repository:'+repo+':pull'))['token']
summary=[]
for task in Path('selected_ids.txt').read_text().splitlines():
 req=urllib.request.Request('https://ghcr.io/v2/'+repo+'/manifests/'+task,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.index.v1+json'})
 try:
  with urllib.request.urlopen(req,timeout=45) as r: raw=r.read();digest=r.headers.get('Docker-Content-Digest')
  data=json.loads(raw);(out/(task+'.index.json')).write_bytes(raw)
  index_digest=digest
  if 'manifests' in data:
   child=next(m for m in data['manifests'] if m.get('platform')=={'architecture':'amd64','os':'linux'})
   req=urllib.request.Request('https://ghcr.io/v2/'+repo+'/manifests/'+child['digest'],headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.oci.image.manifest.v1+json'})
   with urllib.request.urlopen(req,timeout=45) as r: raw=r.read();digest=r.headers.get('Docker-Content-Digest')
   data=json.loads(raw)
  (out/(task+'.json')).write_bytes(raw)
  summary.append({'task':task,'digest':digest,'index_digest':index_digest,'raw_sha256':hashlib.sha256(raw).hexdigest(),'compressed_bytes':sum(x['size'] for x in data.get('layers',[])),'layers':data.get('layers',[]),'manifests':data.get('manifests',[])})
 except Exception as e: summary.append({'task':task,'error':repr(e)})
(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps([{k:v for k,v in x.items() if k!='layers'} for x in summary],indent=2))
unique={l['digest']:l['size'] for x in summary for l in x.get('layers',[])}
print('UNIQUE_COMPRESSED_BYTES',sum(unique.values()))
