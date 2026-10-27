"""Post-session common evaluator; never feeds results to open-loop policy."""
import collections,hashlib,json,shutil,csv,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];BASE=R/Path(os.environ.get('ASPEN_BEHAVIOR_RUN_ROOT','.'));O=BASE/'results/behavior'
read=lambda p:json.loads(p.read_text())
def trajectory(s):return [(s['id']+'_reference',s['baseline'])]+[(i,read(O/'runs'/f'{i}.json')['metrics']) for i in s['records']]
rows=[]
for name,pool in [('appendix_mcm71931','expanded'),('fir_style_12_41_21','initial'),('paper_fig4_mul11','initial')]:
 c=read(O/'sessions'/f'factorial_{name}_{pool}_static_feedback_s0.json');o=read(O/'sessions'/f'openloop_{name}_{pool}_static_openloop_s0.json');assert c['initial_graph_hashes']==o['initial_graph_hashes'];pair={}
 for label,s in [('feedback',c),('openloop',o)]:
  t=trajectory(s);assert len(t)==7;g=[m['gates'] for i,m in t];d=[m['depth'] for i,m in t];ids=[i for i,m in t];hashes=[m['rtl_sha256'] for i,m in t];best=min(g)
  actions=[read(O/'runs'/f'{i}.json')['action'] for i in s['records']];rollback=[j+2 for j,a in enumerate(actions) if a and a['rollback']]
  pair[label]=dict(session_id=s['id'],gates=g,depth=d,rtl_sha256=hashes,last_candidate=dict(id=ids[-1],gates=g[-1],depth=d[-1]),external_best_gates=best,external_best_gate_point_ids=[i for i,m in t if m['gates']==best],unique_rtl=len(set(hashes)),duplicate_query_fraction=(7-len(set(hashes)))/7,rollback_query_numbers=rollback,independent_candidates=False)
 assert pair['feedback']['gates']==pair['openloop']['gates'] and pair['feedback']['depth']==pair['openloop']['depth']
 rows.append(dict(name=name,pool=pool,comparison=pair,paired_response_information_gain_best_gates=0,action_map_divergence_queries=[j+2 for j,(a,b) in enumerate(zip([read(O/'runs'/f'{v}.json')['action'] for v in c['records']],[read(O/'runs'/f'{v}.json')['action'] for v in o['records']])) if a['after']!=b['after']],rollback_note='For x11 divergences after query4 and query7 occur at outer-loop boundaries: query5 resets costs; query7 terminates. No candidate benefit of rollback observed in this budget.',scope='same start, pool, static rule selection, true7-call budget; no assertion of general feedback uselessness'))
(O/'openloop_comparison.json').write_text(json.dumps(rows,indent=2))
ss=[read(p) for p in sorted((O/'sessions').glob('*.json'))];allmetrics=[]
for s in ss:allmetrics+=trajectory(s)
for f in read(O/'figure4.json')['rows']:
 if f['metrics']:allmetrics.append(('figure4_'+f['model'],f['metrics']))
assert len(allmetrics)==367
unique=collections.defaultdict(list)
for ident,m in allmetrics:unique[m['rtl_sha256']].append((ident,m))
assert len(unique)==14
folder=O/'unique_netlists';folder.mkdir(exist_ok=True);inventory=[]
for rtlhash,members in sorted(unique.items()):
 ident,m=members[0];src=BASE/'results/netlists/behavior'/f'{ident}.json';raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==m['netlist_sha256'];dst=folder/f'{rtlhash}.json';dst.write_bytes(raw)
 assert len({(v['gates'],v['depth']) for i,v in members})==1
 inventory.append(dict(rtl_sha256=rtlhash,representative_id=ident,representative_netlist_sha256=m['netlist_sha256'],path=str(dst.relative_to(BASE)),gates=m['gates'],depth=m['depth'],member_count=len(members),member_ids=[i for i,v in members],note='Raw representative JSON includes original source-path metadata; other equal-RTL calls have different raw netlist hashes because source paths differ. No post-synthesis equivalence proof.'))
(O/'unique_netlist_inventory.json').write_text(json.dumps(inventory,indent=2))
old=[m for ident,m in allmetrics if not ident.startswith('openloop_')];fac=[s for s in ss if s['id'].startswith('factorial_')]
q=dict(original_synthesis_calls=346,original_unique_emitted_rtl=len({m['rtl_sha256'] for m in old}),original_duplicate_fraction=(346-len({m['rtl_sha256'] for m in old}))/346,original_factorial_sessions=len(fac),factorial_sessions_with_one_unique=sum(s['unique_rtl']==1 for s in fac),new_openloop_synthesis_calls=21,total_synthesis_calls=367,total_rtl_sat_calls=367,total_unique_emitted_rtl=len(unique),total_duplicate_fraction=(367-len(unique))/367,uniqueness='byte-level emitted RTL SHA256; does not imply distinct logic or independent trials',budget='true EDA invocations matched; unique-design opportunities not matched; reference and repeats charged',incumbent='external common evaluator only; never an output-selection input to the open-loop controller')
(O/'query_diversity.json').write_text(json.dumps(q,indent=2));print(json.dumps(dict(comparisons=rows,diversity=q),indent=2))

with (O/'openloop_summary.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['name','controller','gate_trajectory','depth_trajectory','last_gates','last_depth','external_best_gates','unique_rtl','duplicate_query_fraction'])
 for r in rows:
  for k,v in r['comparison'].items():w.writerow([r['name'],k,str(v['gates']),str(v['depth']),v['last_candidate']['gates'],v['last_candidate']['depth'],v['external_best_gates'],v['unique_rtl'],v['duplicate_query_fraction']])
