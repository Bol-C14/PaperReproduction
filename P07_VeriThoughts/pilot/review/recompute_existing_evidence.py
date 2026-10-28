"""Read-only arithmetic/log review. Does not launch HDL tools or original code."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
R = P / 'runs/attempt1'
checks = []

def observations(name):
    text = (R/name/'oracle/simulate.stdout.log').read_text()
    return [tuple(int(v) for v in line.split()[1:])
            for line in text.splitlines() if line.startswith('OBS ')]

# Re-derive from elementary truth tables and modular closed forms, not the pilot oracle.
truth_tables = {
    'comb_demorgan': [(0,1,1),(1,1,1),(2,1,1),(3,0,0)],
    'comb_mismatch': [(0,0,0),(1,0,1),(2,0,1),(3,1,1)],
    'helper_inline': [(0,0,0),(1,1,1),(2,1,1),(3,0,0)],
}
for name, expected in truth_tables.items():
    got=observations(name)
    assert got==expected,(name,got)
    checks.append(dict(id=name,observations_checked=len(got),method='explicit_four_row_truth_table',
                       first_mismatch=next((x for x in got if x[1]!=x[2]),None)))

for name in ['seq_modular','seq_increment','delayed_pulse']:
    got=observations(name)
    assert [x[0] for x in got]==list(range(261))
    for n,g,c in got:
        if name=='seq_modular': expected=(n%16,(-15*n)%16)
        elif name=='seq_increment': expected=(n%16,(2*n)%16)
        else: expected=(int(n%256==60),0)
        assert (g,c)==expected,(name,n,g,c,expected)
    checks.append(dict(id=name,observations_checked=len(got),method='closed_form_from_zero_initial_state',
                       first_mismatch=next((x for x in got if x[1]!=x[2]),None)))

attempts=json.loads((R/'attempts.json').read_text())
for name in ['empty_discovery','syntax_error']:
    matches=[x for x in attempts if any('/'+name+'/' in s for s in x['argv'])
             and (x['argv'][0]=='iverilog' or '/src/original_driver.py' in x['argv'])]
    assert len(matches)==3
    assert matches[0]['returncode']==0 # Full original evaluator driver exits normally.
    assert [x['returncode'] for x in matches[1:]]==[0,2] # Legal gold / invalid candidate.
    assert 'syntax error' in (R/name/'oracle/candidate.stderr.log').read_text()
    evaluation=[json.loads(x) for x in (R/name/'original/responses_evaluation.jsonl').read_text().splitlines()]
    assert len(evaluation)==1
    if name=='empty_discovery':
        assert evaluation[0]=={'stdout_list':[],'success':True}
        supplied=json.loads((R/name/'original/responses.jsonl').read_text())
        persisted=(R/name/'original/responses/verilog_gen.v').read_text()
        assert supplied['full_response']==persisted=='THIS IS NOT LEGAL VERILOG\n'
    else: assert evaluation[0]['success'] is False and evaluation[0]['stdout_list']==[1]
    checks.append(dict(id=name,method='existing_original_exit_JSON_and_independent_syntax_logs',
                       original_driver_rc=0,golden_iverilog_rc=0,candidate_iverilog_rc=2,
                       official_output=evaluation[0]))

for variant, marker in [('original/yosys_0.stdout.log','SAT proof finished - no model found: SUCCESS!'),
                        ('port/top.stdout.log','SAT proof finished - no model found: SUCCESS!'),
                        ('novel_bound160/top.stdout.log','SAT proof finished - model found: FAIL!')]:
    assert marker in (R/'delayed_pulse'/variant).read_text()
supp=P/'runs/supplemental_logging'
lines=(supp/'yosys.stdout.log').read_text().splitlines()
frame160={x.split()[1]:x.split()[2] for x in lines if len(x.split())==5 and x.split()[0]=='160'}
assert frame160[chr(92)+'gold.count']=='60'
assert frame160[chr(92)+'gold.y']=='1' and frame160[chr(92)+'gate.y']=='0'
assert frame160[chr(92)+'trigger']=='1'
assert json.loads((supp/'command_result.json').read_text())['returncode']==1

blob=(P/'upstream/evaluation_script.py').read_bytes()
blob_id=hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()
assert blob_id=='74963ae51ca6360b5b5944b03c266f7f48309b06'
f=json.loads((P/'freeze.json').read_text())
assert all(hashlib.sha256((P/name).read_bytes()).hexdigest()==sha for name,sha in f['sha256'].items())
print(json.dumps(dict(review_type='existing_logs_and_fixture_semantics_only',new_HDL_or_model_invocations=0,
                     upstream_blob_verified=blob_id,frozen_files_verified=len(f['sha256']),
                     checks=checks,supplemental_witness_rechecked=True,passed=True),indent=2))
