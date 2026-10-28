"""Read anonymous OCI metadata only: never pull layers, credentials, or images."""
import argparse
import hashlib
import json
import pathlib
import urllib.request
import urllib.parse

p = argparse.ArgumentParser()
p.add_argument('--selection', type=pathlib.Path, required=True)
p.add_argument('--output', type=pathlib.Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
results = []
for task in json.loads(a.selection.read_text())['tasks']:
    image = task['image']
    path, tag = image.removeprefix('ghcr.io/').split(':')
    key = path.replace('/', '__') + '__' + tag
    row = {'id': task['id'], 'image': image}
    try:
        query = urllib.parse.urlencode({'service':'ghcr.io','scope':f'repository:{path}:pull'})
        with urllib.request.urlopen('https://ghcr.io/token?' + query, timeout=25) as r:
            token = json.load(r)['token']
        headers = {'Authorization':'Bearer ' + token, 'Accept': ', '.join([
            'application/vnd.oci.image.index.v1+json',
            'application/vnd.docker.distribution.manifest.list.v2+json',
            'application/vnd.oci.image.manifest.v1+json',
            'application/vnd.docker.distribution.manifest.v2+json'])}
        def get(ref):
            req = urllib.request.Request(f'https://ghcr.io/v2/{path}/manifests/{ref}',headers=headers)
            with urllib.request.urlopen(req,timeout=25) as r:
                raw = r.read()
                digest = r.headers.get('Docker-Content-Digest')
            return raw, json.loads(raw), digest
        raw, manifest, digest = get(tag)
        (a.output/(key+'.json')).write_bytes(raw)
        row['tag_digest'] = digest or 'sha256:'+hashlib.sha256(raw).hexdigest()
        if 'manifests' in manifest:
            choices = [x for x in manifest['manifests'] if x.get('platform',{}).get('architecture')=='amd64' and x.get('platform',{}).get('os')=='linux']
            if len(choices)!=1:
                raise ValueError(f'expected one linux/amd64 image; found {len(choices)}')
            row['platform_digest'] = choices[0]['digest']
            raw, manifest, digest = get(row['platform_digest'])
            (a.output/(key+'.amd64.json')).write_bytes(raw)
        else:
            row['platform_digest'] = row['tag_digest']
        row['layers'] = [{'digest':x['digest'],'bytes':x['size']} for x in manifest['layers']]
        row['compressed_layer_bytes'] = sum(x['bytes'] for x in row['layers'])
        row['status'] = 'metadata_audit'
    except Exception as e:
        row['status'] = 'resource_blocked'
        row['error'] = f'{type(e).__name__}: {e}'
    results.append(row)
    (a.output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({k:v for k,v in row.items() if k!='layers'}),flush=True)
layers = {x['digest']:x['bytes'] for row in results for x in row.get('layers',[])}
print(json.dumps({'unique_compressed_layer_bytes':sum(layers.values()),'unique_layers':len(layers)}))
