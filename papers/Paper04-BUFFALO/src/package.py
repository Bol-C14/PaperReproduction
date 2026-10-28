#!/usr/bin/env python3
"""Package only this sanitized checkout and an explicitly supplied matching bundle."""
import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--bundle',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
paper=Path(__file__).resolve().parents[1];repo=paper.parents[1]
head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
refs=subprocess.check_output(['git','bundle','list-heads',str(a.bundle.resolve())],text=True).splitlines()
expected=head+' refs/heads/reproduction/buffalo-iccad2025'
assert refs==[expected],'Refuse a bundle not matching the sanitized public HEAD'
assert (paper/'PUBLICATION_MANIFEST.json').is_file(),'Public export manifest required'
items=[(x,'Paper04-BUFFALO/'+x.relative_to(paper).as_posix()) for x in sorted(paper.rglob('*')) if x.is_file() and '__pycache__' not in x.parts]
items.append((a.bundle.resolve(),'buffalo-iccad2025-public.bundle'))
manifest={name:hashlib.sha256(path.read_bytes()).hexdigest() for path,name in items}
with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as z:
 for path,name in items:z.write(path,name)
 z.writestr('SHA256SUMS.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(a.output) as z:
 assert z.testzip() is None
 for name,h in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==h
print(json.dumps({'path':str(a.output.resolve()),'bytes':a.output.stat().st_size,'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'members_verified':len(manifest),'public_head':head},indent=2))
