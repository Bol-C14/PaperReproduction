"""Serial bounded panel; reject unconfirmed logical changes before expansion."""
import hashlib,json,os,pathlib,subprocess,time
ROOT=pathlib.Path('/workspace/work/rq1-prepilot-20261102')
SRC=pathlib.Path('/workspace/work/fpl26_optimization_contest_ablation_shu/fpl26_contest_benchmarks/vexriscv_re-place_2025.1.dcp')
BASE=ROOT/'contract'
# Remove only generated command/date comment lines, preserving all HDL content.
def canonical(path):
    return '\n'.join(x for x in path.read_text().splitlines() if not x.startswith(('// Date        :','// Command     :','# Command Used:')))
golden=canonical(BASE/'original_funcsim.v')
constraints=canonical(BASE/'original_constraints.xdc')
assert golden==canonical(BASE/'serialized_funcsim.v')
assert constraints==canonical(BASE/'serialized_constraints.xdc')
ledger=ROOT/'panel_ledger.json'
rows=[]
# Calibration already consumed 42 wall seconds. Conservative 45-minute tool-wall cap.
spent=42
# Order frozen before results. Additional confirmation follows only if gate permits.
actions=[('noop_1','noop'),('default_1','Default'),('explore_1','Explore'),('aggressive_1','AggressiveExplore')]
for name,action in actions:
    if spent+600>2700:
        rows.append({'arm':name,'status':'not_run_budget_reservation'});break
    out=ROOT/name;out.mkdir(exist_ok=False)
    cmd=['timeout','--signal=TERM','--kill-after=10s','600s',os.environ['VIVADO_EXEC'],'-mode','batch','-notrace','-source',str(ROOT/'action_arm.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou'),'-tclargs',str(SRC),str(out),action]
    (out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    start=time.monotonic()
    with (out/'stdout.log').open('w') as f:
        r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=out)
    elapsed=time.monotonic()-start;spent+=elapsed
    row={'arm':name,'action':action,'exit_code':r.returncode,'wall_seconds':elapsed,'status':'tool_complete' if r.returncode==0 else ('censored_timeout' if r.returncode in (124,137) else 'tool_failed'),'threads':2,'tool_seed':'not_set_not_claimed_controlled','candidate_selection_seed':None,'input_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'tool_seconds_cumulative':spent}
    if r.returncode==0:
        row['funcsim_identical_to_original']=canonical(out/'funcsim.v')==golden
        row['constraints_identical_to_original']=canonical(out/'constraints.xdc')==constraints
        row['functional_evidence']='identical_exported_functional_representation' if row['funcsim_identical_to_original'] else 'unconfirmed_requires_semantic_checker'
    rows.append(row);ledger.write_text(json.dumps(rows,indent=2)+'\n')
    if r.returncode!=0 or not row.get('funcsim_identical_to_original') or not row.get('constraints_identical_to_original'):
        (ROOT/'STOP_REASON.txt').write_text('Stopped after '+name+': tool/functional-identity/constraint gate requires review. Later arms not run. No model expansion.\n')
        break
print(json.dumps(rows,indent=2))
