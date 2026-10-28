"""Export completed real evidence only; no API, simulator or publication action."""
from pathlib import Path
import argparse
import hashlib
import json
import re

def sha(data):return hashlib.sha256(data).hexdigest()

def export(initial,continuation,destination,intermediate=None):
    destination.mkdir(parents=True,exist_ok=False)
    attempt=continuation/'attempts/001'
    row=json.loads((attempt/'attempt.json').read_text())
    selector=re.search(r'(?m)^\s*\.lib\s+(.+?)\s+tt\s*$',(attempt/'circuit.spice').read_text()).group(1)
    replacements={row['command'][0]:'NGSPICE',selector:'MODEL_SELECTOR'}
    selected=[('continuation',continuation,p) for p in sorted(continuation.rglob('*')) if p.is_file()]
    initial_names=('protocol.json','checks.json','execution_summary.json','guided_failure.json','project_ledger.json')
    selected += [('initial_failure',initial,initial/name) for name in initial_names]
    selected += [('initial_failure',initial,p) for p in sorted((initial/'api').rglob('*')) if p.is_file()]
    if intermediate is not None:
        names=initial_names+('carry_forward_manifest.json','understanding_provenance.json','raw_attempt_map.json')
        selected += [('first_repair',intermediate,intermediate/name) for name in names if (intermediate/name).exists()]
    files=[]
    for group,base,path in selected:
        relative=Path(group)/path.relative_to(base)
        if any(x.startswith('._') or x=='__pycache__' for x in relative.parts):continue
        raw=path.read_bytes();text=raw.decode()
        for private,public in replacements.items():text=text.replace(private,public)
        if path.name.endswith('response.json'):
            obj=json.loads(text)
            if 'id' in obj:obj['id']='REDACTED_PROVIDER_GENERATION_ID'
            text=json.dumps(obj,indent=2,ensure_ascii=False)+'\n'
        if re.search(r'/(?:home|Users)/[^\s"\x27]+',text):raise ValueError('Unrecognized private path in '+str(relative))
        data=text.encode();target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        files.append({'file':str(relative),'source_group':group,'original_sha256':sha(raw),
                      'public_sha256':sha(data),'original_bytes':len(raw),'public_bytes':len(data),
                      'redacted':raw!=data})
    (destination/'EXPORT_MANIFEST.json').write_text(json.dumps({'source_labels':{'initial_failure':initial.name,'continuation':continuation.name},
        'physical_attempts_not_sum_of_carried_copies':len(list((continuation/'attempts').glob('[0-9]*'))),'real_api_attempts_including_failure':10,
        'billing_response_groups':['initial_failure/api','continuation/prior_api','continuation/api'],
        'redactions':['simulator path -> NGSPICE','PDK selector path -> MODEL_SELECTOR','provider generation IDs -> REDACTED_PROVIDER_GENERATION_ID'],
        'scientific_numbers_changed':False,'original_deck_hashes_retained':True,'files':files},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('initial',type=Path);p.add_argument('continuation',type=Path);p.add_argument('destination',type=Path);p.add_argument('--intermediate',type=Path)
    a=p.parse_args();export(a.initial,a.continuation,a.destination,a.intermediate)
