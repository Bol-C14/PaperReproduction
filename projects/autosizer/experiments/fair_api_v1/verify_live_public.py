"""Offline independent verification of portable actual-API pilot evidence."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import math
import sys
from plan import digest
PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT/'experiments/bridge_v1'))
from check import independent_metrics,rescore,waveforms

def verify(root):
    manifest=json.loads((root/'EXPORT_MANIFEST.json').read_text());entries=manifest['files']
    byname={x['file']:x for x in entries}
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    assert actual==set(byname)|{'EXPORT_MANIFEST.json'}, 'Artifact inventory differs from manifest'
    for item in entries:
        data=(root/item['file']).read_bytes()
        assert len(data)==item['public_bytes'] and hashlib.sha256(data).hexdigest()==item['public_sha256']
    current=root/'continuation';rows=[];wave=[]
    for folder in sorted((current/'attempts').glob('[0-9]*')):
        row=json.loads((folder/'attempt.json').read_text());rows.append(row)
        item=byname[str(folder.relative_to(root)/'circuit.spice')]
        assert row['deck_sha256']==item['original_sha256']
        assert row['status'].startswith('valid_')
        metrics=independent_metrics(row,folder);fom,feasible=rescore(metrics)
        assert metrics==row['metrics'] and math.isclose(fom,row['normalized_fom'],rel_tol=1e-12) and feasible==row['feasible']
        if row['mode']=='corrected' and row['export']:wave.append(waveforms(row,folder))
    assert len(rows)==65 and len(wave)==6
    common=json.loads((current/'common.json').read_text());ledger=json.loads((current/'project_ledger.json').read_text())
    guided=json.loads((current/'api_guided_history.json').read_text());control=json.loads((current/'fixed_gp_history.json').read_text())
    assert digest(common)==ledger['common_sha256']
    assert len(common)==10 and len(guided)==24 and len(control)==24
    assert [r['indices'] for r in guided]==[r['indices'] for r in control]
    response_files=[p for name in manifest['billing_response_groups'] for p in (root/name).glob('*/response.json')]
    responses=[json.loads(p.read_text()) for p in response_files]
    assert len(responses)==10
    costs=sum((Decimal(str(r['usage']['cost'])) for r in responses),Decimal(0))
    assert costs==Decimal('.02485815')
    assert all(r['usage']['completion_tokens_details']['reasoning_tokens']==0 for r in responses)
    assert all(r['id']=='REDACTED_PROVIDER_GENERATION_ID' for r in responses)
    report={'public_files_verified':len(entries),'physical_attempts_independently_rescored':65,
            'waveforms_independently_checked':6,'actual_api_responses':10,'cost_usd':str(costs),
            'prompt_tokens':sum(r['usage']['prompt_tokens'] for r in responses),
            'completion_tokens':sum(r['usage']['completion_tokens'] for r in responses),
            'reasoning_tokens':0,'guided_equals_gp_all24':True,'matched_full_budget':True,
            'network_or_simulator_calls_by_verifier':0}
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':verify(Path(sys.argv[1]))
