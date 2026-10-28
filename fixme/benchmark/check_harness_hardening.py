"""Fresh hardening calibration; historical v7/v8 logs are never overwritten."""
import json,pathlib,hashlib
from container_isolation import run_reviewed,authorize_fixture
from fixed_oracle import evaluate_fixed,_evaluate_bound_result
root=pathlib.Path(__file__).resolve().parents[1]/'harness_hardening';plan=json.loads((root/'PLAN.json').read_text());manifest=json.loads((root/'reviewed_manifest.json').read_text());out=root/'results';out.mkdir() # fail closed against overwriting
rows=[]
for trial in plan['trials']:
 entry=manifest['fixtures'][trial['id']];d=root/trial['directory'];files={n:(d/n).read_bytes() for n in entry['files']}
 r=run_reviewed(files,entry['argv'],entry['timeout'],origin='reviewed_local_fixture',fixture_id=trial['id']);decision=evaluate_fixed(r)
 (out/(trial['id'].split('/')[-1]+'.json')).write_text(json.dumps({'container':r,'decision':decision},indent=2)+'\n')
 assert r['container_removed'],r
 assert decision['status']==trial['expected'],(trial,decision)
 if trial['id'].endswith('client_output_flood'):assert r['status']=='output_limit',r
 if trial['id'].endswith('outer_timeout'):assert r['status']=='timeout',r
 rows.append({'id':trial['id'],'expected':trial['expected'],'actual':decision,'container_status':r['status'],'seconds':r['seconds']})
entry=manifest['fixtures']['hardening/correct_mux'];d=root/'fixtures/correct_mux';files={n:(d/n).read_bytes() for n in entry['files']}
rejects=[]
for name,origin,id,fs,argv in [('missing_origin',None,'hardening/correct_mux',files,entry['argv']),('unknown_origin','unknown','hardening/correct_mux',files,entry['argv']),('model_generated_origin','model_generated','hardening/correct_mux',files,entry['argv']),('modified_bytes','reviewed_local_fixture','hardening/correct_mux',dict(files,**{'dut.sv':files['dut.sv']+b'\n'}),entry['argv']),('modified_argv','reviewed_local_fixture','hardening/correct_mux',files,['sh']),('missing_fixture_id','reviewed_local_fixture',None,files,entry['argv'])]:
 try:authorize_fixture(fs,argv,5,origin,id)
 except ValueError as e:rejects.append({'control':name,'rejected_before_docker':True,'reason':str(e)})
 else:raise AssertionError(name)
# Synthetic tool-state envelopes exercise taxonomy, not real tool results.
controls=[({'state':'timeout','returncode':-9,'stderr':''},'unknown'),({'state':'output_limit','returncode':-9,'stderr':''},'unknown'),({'state':'completed','returncode':-9,'stderr':'killed'},'unknown'),({'state':'completed','returncode':127,'stderr':'tool missing'},'unknown'),({'state':'completed','returncode':2,'stderr':'syntax error'},'task_syntax_failure'),({'state':'completed','returncode':1,'stderr':'internal tool crash'},'unknown')]
tax=[]
for c,expected in controls:
 r={'status':'completed','returncode':0,'oracle_policy':'trusted_fixed_mux_trace','stdout':json.dumps({'compile':c})};v=_evaluate_bound_result(r);assert v['status']==expected;tax.append({'synthetic_compile_state':c,'decision':v})
summary={'schema_version':1,'run_type':'fresh_hardening_calibration_not_historical_replay','container_executions':len(rows),'trials':rows,'pre_execution_rejections':rejects,'synthetic_taxonomy_tests':tax,'model_calls':0,'paid_resources':0,'historical_evidence_unchanged':True,'sum_wrapper_elapsed_seconds':round(sum(r['seconds'] for r in rows),4)}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['trials','synthetic_taxonomy_tests','pre_execution_rejections']}))

# A hand-crafted host dictionary is not accepted as an authorized run record.
assert evaluate_fixed({'status':'completed','returncode':0,'oracle_policy':'trusted_fixed_mux_trace','stdout':'CHECK_PASS checks=4'})['status']=='unknown'
