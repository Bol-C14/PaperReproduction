"""Local-only payload provenance/freeze. Contains no network transport or credentials."""
import hashlib,json,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'plans/online_pilot'
CASES=[('case_A','appendix_mcm71931',12),('case_B','mcm593',16)]
ALLOWED={'Add','Sub','Mul','Shl','Num','Var'}
FROZEN={
 'appendix_mcm71931':('8f5403a33ff924d76312491fa781485cf6ddc8c674d8d80e7bbc5fbeec8bdaaf','f9def5799bd6b05de3ccaa81f4683e41c6d1c2375ea0c36f47c6de341625bd91'),
 'mcm593':('457cf81f30ad4a526c057811df7dece74ece226a5ea2b60c0467b6978985e261','2e620056dd92acd348c7d5432016b2844b9ecfcf032b4d8c651c07701944f5a2')}
def validate_source(p,expected):assert sha(p)==expected, 'Source is not the reviewed synthetic artifact; stop for new provenance review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def assert_payload(p):
 assert set(p)=={'schema','case','width','semantics','graph','selected_nodes','node_costs','attributed_cells','observations','action_space','goal'}
 assert p['case'] in ['case_A','case_B'] and p['width'] in [12,16]
 for n in p['graph']['nodes']:
  assert set(n)<= {'id','eclass','op','children','value'} and n['op'] in ALLOWED|{'LiteralInt','LiteralVar'}
  if n['op']=='LiteralVar':assert n['value'] in ['x','x0','x1','x2']
 blob=json.dumps(p,sort_keys=True)
 for bad in ['/workspace/','/home/','https://','http://','Authorization','api_key','credential','repository','commit','file_id','library_file_id']:assert bad not in blob,bad
 for row in p['observations']:assert set(row)=={'query','generic_gates','generic_depth'}
 assert len(blob.encode())<=32768
 return len(blob.encode())
def main():
 started=time.perf_counter();manifest=[]
 for alias,name,w in CASES:
  gp=ROOT/f'results/attribution_round/graphs/{name}.json';rp=ROOT/f'results/attribution_round/runs/{name}_w{w}_openloop_q0.json';validate_source(gp,FROZEN[name][0]);validate_source(rp,FROZEN[name][1]);g=json.loads(gp.read_text());r=json.loads(rp.read_text());ids=sorted(g['nodes']);classes=sorted({v['eclass'] for v in g['nodes'].values()});im={x:f'n{i:03}' for i,x in enumerate(ids)};cm={x:f'e{i:03}' for i,x in enumerate(classes)};nodes=[]
  for ident in ids:
   n=g['nodes'][ident];op=n['op'];new=dict(id=im[ident],eclass=cm[n['eclass']],op=op,children=[im[c] for c in n['children']])
   if op not in ALLOWED:
    if re.fullmatch(r'-?\d+',op):new.update(op='LiteralInt',value=int(op))
    else:new.update(op='LiteralVar',value=json.loads(op))
   nodes.append(new)
  p=dict(schema='cost-action-v1',case=alias,width=w,semantics='All values and intermediates unsigned modulo 2^W; nonnegative integer shift counts; no X/Z or sequential state.',graph=dict(nodes=nodes,roots=[cm[c] for c in g['root_eclasses']]),selected_nodes=[im[n] for n in r['extraction']['used_nodes'] if g['nodes'][n]['op'] in {'Add','Sub','Mul','Shl'}],node_costs={im[n]:v for n,v in r['costs_before'].items()},attributed_cells={im[n]:v for n,v in r['metrics']['attribution'].items()},observations=[dict(query=0,generic_gates=r['metrics']['gates'],generic_depth=r['metrics']['depth'])],action_space=dict(kind='choose_one',choices=['increase_selected_node_by_3','decrease_selected_node_by_3_floor_0.25','restore_last_accepted_cost_snapshot'],max_cost=64,reply_keys=['action','node'],extra_keys_forbidden=True),goal='Minimize generic gate count. Choose one bounded cost action for the next extraction. No code generation. Depth is secondary reporting, not physical delay.')
  size=assert_payload(p);target=OUT/'payloads'/f'{alias}_q0.example.json';target.write_text(json.dumps(p,indent=2));manifest.append(dict(case_alias=alias,payload_file=str(target.relative_to(ROOT)),payload_sha256=sha(target),compact_payload_bytes=size,content_classification='synthetic mathematical circuit + locally generated synthetic measurements; not private design content, not a publication or transmission authorization',field_provenance={'case':'new local alias; no original fixture/repository name','width':'existing controlled fixture definition','semantics':'locally authored mathematical assumptions','graph':{'source':str(gp.relative_to(ROOT)),'sha256':sha(gp),'transform':'whitelist operations/literals, anonymous node/eclass aliases, drop metadata and original IDs'},'selected_nodes/node_costs/attributed_cells':{'source':str(rp.relative_to(ROOT)),'sha256':sha(rp),'transform':'numeric fields only, alias IDs; no RTL/netlist/file paths or logs'},'observations':'query0 gate/depth from synthetic existing run; future values must come only from each arm own actual query history','action_space/goal':'new protocol text and fixed bounded action schema'},excluded=['private repository identity/remote/commit/paths','full source/scripts/comments','raw netlists and logs with path metadata','private uploaded data','conversation content','all credentials/headers'],transmission_authorized=False,transmitted=False))
 protocol=dict(status='LOCAL_FROZEN_MECHANICS; provider binding and transmission BLOCKED',parent_commit='cf6b2eca53ea03220377e78d286b9825bca186ac',v3_archive=dict(path='/workspace/deliverables/aspen-mlcad2025-review.zip',sha256=sha(ROOT.parent/'deliverables/aspen-mlcad2025-review.zip'),preserve_unchanged=True),cases=[dict(alias=a,fixture=n,width=w) for a,n,w in CASES],arms=['online_cost_action','verified_structural_openloop'],matched=dict(frozen_graph=True,same_existing_rule_pool=True,initial_costs='operator1/leaf0',novelty='existing bounded e-node exclusion; no arm-internal repeated tagged RTL',synthesis_calls_per_arm=6,rtl_sat_calls_per_arm=6,reference_in_budget=True,future_total_synthesis=24,future_total_rtl_sat=24,cache=False),future_model_budget=dict(current_authorized_calls=0,current_authorized_transmissions=0,proposed_max_calls_if_later_authorized=10,actions_after_queries=[0,1,2,3,4],no_terminal_action=True,max_output_tokens_per_call=128,retries=0,invalid_or_missing_action='stop arm; record failure; do not silently repair or refill quota'),binding=dict(endpoint=None,provider=None,model=None,verified_free_quota=None,credential_source='not read, persisted or included; parent generic authentication test is separate'),controller=dict(online='strict JSON one bounded action among selected nodes; persistent state; accepted snapshots; no generated proof/code execution',openloop='existing structural_node, +3 only, no response/history input',cost_floor=.25,cost_ceiling=64,rule_proposal='disabled; published existing replay pool fixed',rule_selection='fixed; model controls costs only',attribution='existing deterministic named-wire cone allocation; not LLM netlist attribution'),stopping=dict(max_one_seed=0,fixtures=2,coverage='cell>=0.6 and named operator>=0.8; terminate failed arm, no fixture replacement in this pilot',no_use_of_private_inputs=True,no_unbounded_sweeps=True),evaluation=dict(primary='same external best generic gates over actual queries incl reference, paired depth/pointIDs retained',algorithm_output='last emitted candidate separately; do not let openloop use response to select returned RTL',report=['unique RTL and metric pairs','duplicate/cross-arm overlap','actual EDA/SAT/model calls including failures','all time: graph/features/attribution/model/controller/novelty/EDA','API input/output tokens and known price, unknown explicitly unknown','rollback next-candidate causal trace'],claims='No original commercial PPA or complete ASPEN/LLM-attribution claim'),execution_now=dict(model_calls=0,new_synthesis_calls=0,new_rtl_sat_calls=0,paid_cost_usd=0,repository_data_transmissions=0,local_preparation_seconds=time.perf_counter()-started),source_hash_allowlist=FROZEN,provenance_boundary='Anonymizing a private graph does not make it public; only these exact reviewed synthetic graphs and their own verified synthetic observations are allowed. Provider/auth HTTP envelope is not yet specified or authorized.',exact_blockers=['No provider/endpoint/model/free quota binding verified here','No model-call or data-transmission allocation; pasted credential alone is not free-quota evidence','No network adapter implemented; dry-run preparer has no transport','Future observed values not yet available: only example q0 bytes frozen; dynamic schema/provenance frozen'])
  # Keep provider-specific/auth envelope out of all payload examples.
 (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2));(OUT/'payload_provenance.json').write_text(json.dumps(manifest,indent=2))
 # Negative cases prove accidental source/secret fields fail the allowlist, using dummy data only.
 tests=0
 for f in (OUT/'payloads').glob('*.json'):
  p=json.loads(f.read_text());assert_payload(p);tests+=1
  bad=dict(p);bad['private_path']='dummy'
  try:assert_payload(bad)
  except AssertionError:tests+=1
  else:raise AssertionError('extra field accepted')
 tamper_tests=0
 for alias,name,w in CASES:
  path=ROOT/f'results/attribution_round/graphs/{name}.json'
  try:validate_source(path,'0'*64)
  except AssertionError:tamper_tests+=1
  else:raise AssertionError('changed provenance accepted')
 report=dict(schema_tests_passed=tests,source_hash_checks_passed=4,source_hash_tamper_tests_passed=tamper_tests,examples=2,network_requests=0,model_requests=0,new_eda_calls=0,paid_cost_usd=0,transmissions=0,credential_read=False,credential_persisted=False)
 (ROOT/'logs/online_pilot/local_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
