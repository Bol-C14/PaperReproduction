"""Recompute public summary from private preserved raw evidence; no task execution."""
import csv
from public_sanitize import public_view
import hashlib
import json
from pathlib import Path

B=Path(__file__).resolve().parents[1]
E=B/'.private/evidence'
R=E/'results/terminal-bench'
M=json.loads((B/'manifest.json').read_text())
rows=json.loads((R/'run-v7/summary.json').read_text())
if len(rows)!=13: raise RuntimeError('Incomplete frozen matrix plus alternative')
if any(r['status']=='resource_blocked' for r in rows): raise RuntimeError('Final batch has unresolved infrastructure failure')
public=[]
for r in rows:
    d={k:r.get(k) for k in ['id','task','agent','cpu_affinity','memory_mb','status','port','timings_sec','timeouts','verifier','independent','independent_exit','artifact_sha256','timeout_probe','stale_reward_seeded','cleanup_error'] if k in r}
    d['ctrf_summary']=r.get('ctrf',{}).get('results',{}).get('summary')
    pre=r['preflight']
    d['resources']={k:pre[k] for k in ['affinity','memory_max','pids_max','controllers','status','interfaces','python','hidden_paths']}
    assert pre['memory_max']=='2147483648' and pre['pids_max']=='128'
    assert pre['affinity']==([0] if r['cpu_affinity']=='0' else [0,1])
    assert pre['interfaces']==['lo'] and not any(pre['hidden_paths'].values())
    assert any(s.startswith('CapEff:') and s.split()[-1]=='0000000000000000' for s in pre['status'])
    assert any(s.startswith('NoNewPrivs:') and s.split()[-1]=='1' for s in pre['status'])
    public.append(d)
failed=[]
for p in sorted(R.rglob('result.json')):
    if p.parent.parent.name=='run-v7': continue
    x=json.loads(p.read_text())
    failed.append({'path':str(p.relative_to(E)),'id':x['id'],'status':x['status'],'error':x.get('error'),'verifier':x.get('verifier'),'timings_sec':x['timings_sec']})
resets={}
for t in M['dataset']['selected_tasks']:
    inputs=[r['preflight']['inputs'] for r in rows if r['task']==t]
    resets[t]={'fresh_trials':len(inputs),'identical_initial_inputs':all(x==inputs[0] for x in inputs),'input_files':len(inputs[0]),'input_manifest_sha256':hashlib.sha256(json.dumps(inputs[0],sort_keys=True).encode()).hexdigest()}
assert all(x['identical_initial_inputs'] for x in resets.values())
meta=json.loads((E/'assets/terminal-bench/metadata.json').read_text())
changed={}
for path,h in meta['selection']['sha256'].items():
    if meta['ports'][path]['sha256']!=h: changed[path]={'original':h,'port':meta['ports'][path]['sha256']}
assert all(p.endswith(('task.toml','tests/test.sh','log-summary-date-ranges/solution/solve.sh')) for p in changed)
assert not any(p.endswith(('test_outputs.py','test.py')) for p in changed)
isolation=json.loads((E/'logs/terminal-bench/isolation-inventory.json').read_text())
assert all(not x['exact_forbidden_content_matches'] and not x['git_paths'] for x in isolation)
summary={'controls':public,'infrastructure_or_incomplete_attempts':failed,'reset_reproducibility':resets,'changed_task_files':changed,'assertion_files_unchanged':True,'isolation_scan':[{'task':x['task'],'scanned_files':len(x['files']),'git_paths':x['git_paths'],'exact_forbidden_content_matches':x['exact_forbidden_content_matches']} for x in isolation]}
private_root = str(Path(meta['repositories']['dataset']['commit']['argv'][2]).parents[2])
(B/'metrics/calibration.json').write_text(json.dumps(public_view(summary,private_root),indent=2)+'\n')
with (B/'metrics/resource_comparison.csv').open('w',newline='') as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['task','affinity_cpus','upstream_reward','independent_pass','solution_wall_sec','verifier_wall_sec','total_wall_sec'])
    for x in public:
        if x['agent']=='oracle': w.writerow([x['task'],len(x['resources']['affinity']),x['verifier']['rewards']['reward'],x['independent']['passed'],x['timings_sec']['solution'],x['timings_sec']['verifier'],x['timings_sec']['total']])
for t in M['dataset']['selected_tasks']:
    img=json.loads((E/f'logs/terminal-bench/image-{t}.json').read_text())[0]
    M['images'][t]['original_repo_digests']=img.get('RepoDigests',[])
    M['images'][t]['original_image_id']=img['Id']
M['status_by_scope']['reference_controls']='reference_calibration'
M['status_by_scope']['negative_and_alternative_controls']='offline_replay'
M['result_counts']={'final_main_cells':12,'reference_cells':6,'noop_cells':6,'alternative_cells':1,'additional_infrastructure_or_partial_records':len(failed),'model_calls':0}
M['budget_accounting']={'main_grid_completed':12,'additional_alternative':1,'setup_and_partial_attempt_records':len(failed),'attempt_cap_note':'The predeclared 12 main-cell grid was completed. Infrastructure retries produced additional attempt records, including partial no-op runs; an absolute all-attempt cap was not enforced. No model/paid experiment occurred.','setup_hours_under_2':True}
M['registry']={'repository_commit':M['harness']['commit'],'path':'registry.json','entry':'terminal-bench@2.0','task_count':89}
M['results_file']='metrics/calibration.json'
M['resource_comparison']='metrics/resource_comparison.csv'
(B/'manifest.json').write_text(json.dumps(public_view(M,private_root),indent=2)+'\n')
print(json.dumps({'final_controls':len(public),'extra_attempt_records':len(failed),'upstream_oracle_rewards':[x['verifier']['rewards']['reward'] for x in public if x['agent']=='oracle'],'independent_oracle_passes':[x['independent']['passed'] for x in public if x['agent']=='oracle'],'reset':resets,'timeout_probe':[x['timeout_probe'] for x in public if 'timeout_probe' in x]},indent=2))
