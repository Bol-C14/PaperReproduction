"""Verify reference-calibration evidence and build final all-482 state matrix."""
import argparse,collections,csv,hashlib,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--audit',required=True);p.add_argument('--batch',required=True);p.add_argument('--output',required=True);a=p.parse_args();audit=json.loads(pathlib.Path(a.audit).read_text());base=pathlib.Path(a.batch);batch=json.loads((base/'results.json').read_text());out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
code={r['id']:r for r in batch['results']};assert len(code)==231
expected={r['id'] for r in audit['cases'] if r['subset'] in ['MGen','TBGen','SVAGen'] or(r['subset']=='RTLFix' and r['modality']=='MultiModal')};assert set(code)==expected
matrix=[];event_count=0
for row in audit['cases']:
 result={'id':row['id'],'subset':row['subset'],'schema_original_complete':row['schema_complete'],'schema_structural_complete':row['adapted_schema_complete'],'input_overlay_count':len(row['structural_overlays']),'input_missing':row['adapted_missing_required'],'live_llm':False,'is_model_score':False,'prior_pilot_input':row['prior_pilot_input']}
 if row['id'] in code:
  r=code[row['id']];evidence_root=base/r.get('evidence_root','.');work=evidence_root/r['subset']/('case_'+hashlib.sha256(r['id'].encode()).hexdigest()[:12]);events=[json.loads(x) for x in (work/'trace.jsonl').read_text().splitlines()];assert len(events)==r['commands'];event_count+=len(events)
  for e in events:
   assert (evidence_root/e['log']).is_file()
   if e['status']=='timeout':assert e['returncode'] is None
  if r['status']=='pass':
   assert all(e['status']=='completed' for e in events)
   assert r['negative_control_detected'] is True and r['functional_pass'] is True
   assert len(events)>=4
   if r['subset']=='SVAGen':
    assert r['property_counts']['assert']>0
    assert r['constant_control_status']=='unknown'
    assert r['constant_mutation_killed'] is False
    from evaluation import property_counts
    assert property_counts(work/'positive.json')['assert']==r['property_counts']['assert']
    assert any('proof did fail' in (evidence_root/e['log']).read_text(errors='replace').lower() for e in events if 'negative_rtl' in e['log'])
    for key in ['constant_control','constant_mutant_control']:
     matching=[e for e in events if e['log'].endswith(key+'.log')]
     assert len(matching)==1 and matching[0]['returncode']==0
     assert 'SUCCESS!' in (evidence_root/matching[0]['log']).read_text(errors='replace')
  else:assert r['functional_pass'] is None
  result['ever_tools_executed']=any(h['commands']>0 for h in r.get('attempt_history',[{'commands':r['commands']}]))
  result['attempt_history']=r.get('attempt_history',[])
  result.update(adapter_status=r['status'],tool_commands=len(events),tools_executed=bool(events),negative_control_detected=r['negative_control_detected'],reason=r.get('reason'),reference_status=r.get('reference_status'),eda_attempt='tool_invoked' if events else 'preflight_only',result_path=str((work/'result.json').relative_to(base)))
  timeouts=sum(e['status']=='timeout' for e in events);result['command_timeouts']=timeouts
  resource_limited=any(e['returncode'] in [-24,-25,-9] for e in events if e['status']=='completed')
  if r['status']=='pass':result['final_state']='reference_calibration_pass'
  elif r['status']=='adapter_unsupported':result['final_state']='adapter_contract_unsupported'
  elif timeouts:result['final_state']='timeout_unknown'
  elif r['status']=='unknown' and resource_limited:result['final_state']='resource_or_external_kill_unknown'
  elif r['status']=='unknown':result['final_state']='proof_or_oracle_unknown'
  elif 'missing' in r.get('reason','').lower() and ('asset' in r.get('reason','').lower() or 'include' in r.get('reason','').lower()):result['final_state']='data_dependency_error'
  else:result['final_state']='reference_or_adapter_error'
 else:
  controls=row.get('reference_controls',[]);assert len(controls)==3
  complete=row['adapted_schema_complete'];pos=controls[0]['status'];result.update(tool_commands=0,tools_executed=False,negative_control_detected=all(x['status']=='fail' for x in controls[1:]),eda_attempt='not_applicable_to_official_text_matcher',reason='reference-only scorer, no generated model output or RTL repair execution')
  result['final_state']='reference_scorer_checked' if complete and pos=='pass' else 'data_or_reference_error'
 matrix.append(result)
summary={'kind':'all-public-case-coverage-not-model-results','public_cases':len(matrix),'model_results':0,'code_adapter_cases':len(code),'code_tool_invoked':sum(r['commands']>0 for r in code.values()),'code_preflight_only':sum(r['commands']==0 for r in code.values()),'code_ever_tool_invoked':sum(any(h['commands']>0 for h in r.get('attempt_history',[{'commands':r['commands']}])) for r in code.values()),'total_recorded_command_attempts':sum(sum(h['commands'] for h in r.get('attempt_history',[{'commands':r['commands']}])) for r in code.values()),'code_commands':event_count,'code_by_subset':{s:dict(collections.Counter(r['status'] for r in code.values() if r['subset']==s)) for s in ['MGen','TBGen','SVAGen','RTLFix']},'final_states':dict(collections.Counter(r['final_state'] for r in matrix)),'schema_complete_structural':sum(r['schema_structural_complete'] for r in matrix),'unattempted_code_cases':0,'scope_note':'adapter attempts include explicit content-based preflight refusals. Tools executed is reported separately. Reference-derived fixtures calibrate evaluators and are not independent functional verification or LLM scores.'}
(out/'matrix.json').write_text(json.dumps({'summary':summary,'cases':matrix},indent=2))
with (out/'matrix.csv').open('w') as f:
 fields=list(dict.fromkeys(k for r in matrix for k in r));writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(matrix)
(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print('PASS: 482 final case states and all batch command/control links verified')
