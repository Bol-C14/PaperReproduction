"""Offline, tool-free evidence checks and derived metrics for the bounded pilot."""
import csv,hashlib,json,pathlib,collections,difflib
root=pathlib.Path(__file__).resolve().parents[1]/'evaluator_validity'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((root/'pilot_1/results.json').read_text());repair=json.loads((root/'tb_vector_repair/results.json').read_text())
assert len(base['results'])==63 and len(repair['results'])==14
assert base['preregistration_plan_sha256']==h(root/'plan.json')
selected=[(root/'pilot_1',r) for r in base['results'] if r['family']!='TBGen']+[(root/'tb_vector_repair',r) for r in repair['results']]
assert len(selected)==63
for directory,rows in [(root/'pilot_1',base['results']),(root/'tb_vector_repair',repair['results'])]:
 for r in rows:
  d=r['injection_diff'];assert h(directory/d['path'])==d['sha256']
  e=r.get('simulation_event',r.get('event',r.get('compile_event')));assert (directory/e['log']).exists()
  if e['status']=='timeout':assert r['decision']['status']=='unknown'
  w=(directory/d['path']).parent
  if (w/'response.cpp').exists():assert h(w/'response.cpp')==r.get('source_sha256',h(w/'response.cpp'))
  if (w/'property.sv').exists():
   assert h(w/'property.sv')==r['property_sha256']
   original='always @* assert(crc_o[5] == crc_i[13]);'
   if r['oracle']=='all_outputs':original=(w/'property.sv').read_text()
   patch=''.join(difflib.unified_diff(original.splitlines(True),(w/'property.sv').read_text().splitlines(True),fromfile='baseline_property.sv',tofile='candidate_property.sv'))
   (w/'property_injection.diff').write_text(patch)
   if r['property_counts'] is not None:
    modules=json.loads((w/'properties.json').read_text())['modules'];n=sum(c['type'] in ('$assert','$check') for m in modules.values() for c in m.get('cells',{}).values())
    assert n==r['property_counts']['assert']
   if r['decision']['raw_proof']=='vacuous_zero_properties':assert r['decision']['status']=='unknown'
# Same literal TB vectors and same DUT bytes for paired backends.
pairs=collections.defaultdict(list)
for directory,r in selected:
 if r['backend'] in ('icarus','verilator'):pairs[(r['family'],r['variant'],r['oracle'])].append(r)
for key,rs in pairs.items():
 assert len(rs)==2 and rs[0]['bench_sha256']==rs[1]['bench_sha256'] and rs[0]['source_sha256']==rs[1]['source_sha256']
 assert rs[0]['decision']==rs[1]['decision'],key
assert len(pairs)==19
m=[r for _,r in selected if r['family']=='MGen' and r.get('activation') and r['activation']['changed_calls']>0]
survivors=[r['variant'] for r in m if r['decision']['status']=='pass']
metrics={'primary_trials':63,'compatibility_retries':14,'actual_trial_executions':77,'independent_designs':4,'commands':base['supervised_command_attempts']+repair['supervised_command_attempts'],'execution_wall_seconds_sum':round(base['wall_seconds']+repair['wall_seconds'],3),'model_api_calls':0,'cross_simulator_identical_input_pairs':len(pairs),'cross_simulator_equal_decisions_and_counts':len(pairs),'ga94_activated_functional_injections':len(m),'ga94_activated_survivors':survivors,'not_a_population_false_positive_rate':True,'sva_constant_proof_adequacy':'unknown: property is constant and survives covered mutant; raw successful proofs retained','status_counts':dict(collections.Counter(r['decision']['status'] for _,r in selected))}
assert metrics['commands']<=150
iso=json.loads((root/'pilot_1/isolation.json').read_text())['probe'];assert iso['synthetic_env_absent'] and iso['network_denied'];assert iso['sibling_read_allowed'] and iso['sibling_write_allowed']
(root/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
with (root/'selected_trials.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['family','design','variant','backend','oracle','raw_status','adequacy_note','evidence_root'])
 for d,r in selected:w.writerow([r['family'],r['design'],r['variant'],r['backend'],r['oracle'],r['decision']['status'],'unknown_constant_property' if r['oracle']=='constant' else 'scope_limited' if r['family']=='SVAGen' else '',str(d.relative_to(root))])
print(json.dumps(metrics,indent=2))
