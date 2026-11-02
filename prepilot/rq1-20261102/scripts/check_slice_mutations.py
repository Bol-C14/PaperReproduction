"""Small local negative controls for the narrow checker; never edits raw logs."""
from pathlib import Path
import json,shutil,subprocess,sys,tempfile
P=Path(__file__).resolve().parents[1]
old=(P/'logs/contract/original_funcsim.v').read_text();new=(P/'logs/default_1/funcsim.v').read_text()
# Deliberate local HDL mutations; these are checker controls, not actual DCP runs.
cases=[('actual_pair',new,True),('changed_LUT_INIT_bit',new.replace(".INIT(64'h4545404055005500)",".INIT(64'h4545404055005501)",1),False),('changed_new_LUT_input',new.replace('.I0(writeBack_arbitration_isValid),\n        .I1(memory_to_writeBack_IS_MUL),\n        .O(\\HazardSimplePlugin_writeBackWrites_payload_data[18]_repN )','.I0(_zz_8),\n        .I1(memory_to_writeBack_IS_MUL),\n        .O(\\HazardSimplePlugin_writeBackWrites_payload_data[18]_repN )',1),False),('unaccounted_remaining_logic_change',new.replace(".INIT(64'hEAFFFFFFEA000000)",".INIT(64'hEAFFFFFFEA000001)",1),False),('extra_unaccounted_wire',new.replace('module DataCache\n','wire unexpected_wire;\nmodule DataCache\n',1),False)]
rows=[]
with tempfile.TemporaryDirectory(prefix='rq1-slice-controls-') as tmp:
 root=Path(tmp);(root/'scripts').mkdir();(root/'logs/contract').mkdir(parents=True);(root/'logs/default_1').mkdir(parents=True)
 shutil.copy2(P/'scripts/prove_default_lut_slice.py',root/'scripts/prove_default_lut_slice.py')
 (root/'logs/contract/original_funcsim.v').write_text(old)
 for name,text,expected in cases:
  assert expected or text!=new, 'mutation did not apply: '+name
  (root/'logs/default_1/funcsim.v').write_text(text)
  r=subprocess.run([sys.executable,str(root/'scripts/prove_default_lut_slice.py')],capture_output=True,text=True,timeout=10)
  passed=r.returncode==0
  rows.append({'case':name,'expected_accept':expected,'accepted':passed,'matches_expectation':passed==expected,'exit_code':r.returncode,'last_error':r.stderr.splitlines()[-1] if r.stderr else None})
assert all(r['matches_expectation'] for r in rows),rows
(P/'SLICE_MUTATION_CONTROLS.json').write_text(json.dumps({'scope':'local_exported_HDL_checker_controls_only_no_EDA_runs','results':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2))
