"""Export the completed run with exact originals hashed and runtime paths replaced.
No model bytes, credentials, source archives, environments or metadata are selected.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

def digest(data):return hashlib.sha256(data).hexdigest()

def export(source,destination):
    destination.mkdir(parents=True,exist_ok=False)
    attempts=sorted((source/'attempts').glob('*/attempt.json'))
    if len(attempts)!=53:raise ValueError('Expected complete 53-attempt run')
    first=json.loads(attempts[0].read_text())
    deck=(attempts[0].parent/'circuit.spice').read_text()
    selector=re.search(r'(?m)^\s*\.lib\s+(.+?)\s+tt\s*$',deck).group(1)
    replacements={first['command'][0]:'NGSPICE',selector:'MODEL_SELECTOR'}
    manifest=[]
    for path in sorted(source.rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(source)
        if any(part.startswith('._') or part=='__pycache__' for part in relative.parts):continue
        if path.suffix not in ('.json','.txt','.log','.tsv','.spice'):
            raise ValueError('Unexpected artifact type: '+str(relative))
        raw=path.read_bytes()
        text=raw.decode()
        for original,public in replacements.items():text=text.replace(original,public)
        if re.search(r'/(home|Users)/[^\s"\x27]+',text):
            raise ValueError('Unrecognized runtime path in '+str(relative))
        public=text.encode()
        out=destination/relative
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes(public)
        manifest.append({'file':str(relative),'original_sha256':digest(raw),
                         'public_sha256':digest(public),'original_bytes':len(raw),'public_bytes':len(public),
                         'runtime_paths_replaced':raw!=public})
    (destination/'EXPORT_MANIFEST.json').write_text(json.dumps({
        'transformations':['simulator executable path -> NGSPICE','PDK selector path -> MODEL_SELECTOR'],
        'scientific_numbers_changed':False,'original_deck_sha256_retained_in_attempt_json':True,
        'files':manifest},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    a=p.parse_args();export(a.source,a.destination)
