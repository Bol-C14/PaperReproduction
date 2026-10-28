"""Verify the portable evidence without network or simulator calls."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import check

def verify(root):
    manifest=json.loads((root/'EXPORT_MANIFEST.json').read_text())
    files=manifest['files']
    for item in files:
        data=(root/item['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==item['public_sha256']
        assert len(data)==item['public_bytes']
        if not item['runtime_paths_replaced']:assert item['public_sha256']==item['original_sha256']
    by_name={f['file']:f for f in files}
    rows=[]
    waveform_checks=0
    for folder in sorted((root/'attempts').glob('[0-9]*')):
        row=json.loads((folder/'attempt.json').read_text());rows.append(row)
        item=by_name[str(folder.relative_to(root)/'circuit.spice')]
        assert row['deck_sha256']==item['original_sha256']
        assert row['command']==['NGSPICE','-n','-b','circuit.spice']
        assert row['status'].startswith('valid_')
        m=check.independent_metrics(row,folder)
        assert m==row['metrics']
        fom,feasible=check.rescore(m)
        assert math.isclose(fom,row['normalized_fom'],rel_tol=1e-12)
        assert feasible==row['feasible']
        if row['mode']=='corrected' and row['export']:
            check.waveforms(row,folder);waveform_checks+=1
    assert len(rows)==53 and waveform_checks==4
    assert json.loads((root/'checks.json').read_text())['passed']
    print(json.dumps({'public_files_verified':len(files),'raw_attempts_rescored':53,
                      'independent_waveforms_verified':4,'network_calls':0}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path)
    verify(p.parse_args().root)
