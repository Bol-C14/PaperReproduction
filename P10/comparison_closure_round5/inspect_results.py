"""Read-only post-selection checks; no solvers, synthesis, or external calls."""
import hashlib,json,subprocess,sys
from pathlib import Path

# Reuse the independently authored standard-library DAG/netlist recount, not
# the experiment's extractor or measurement implementation.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nested_combine_round4'))
from inspect_results import netlist_cost,selected_cost

def inspect(root):
 manifest=json.loads((root/'manifest.json').read_text())
 for name,digest in manifest['files'].items():
  data=subprocess.check_output(['git','show',manifest['git_head']+':P10/comparison_closure_round5/'+name])
  assert hashlib.sha256(data).hexdigest()==digest,name
 summary=json.loads((root/'summary.json').read_text());audit=json.loads((root/'audit.json').read_text())
 assert summary['pass'] and audit['pass'] and len(summary['rows'])==2
 checks=[]
 def has_scoped_one(t):
  return isinstance(t,list) and (t[:3]==['Assume',1,['K',1,1]] or any(has_scoped_one(c) for c in t))
 for row in summary['rows']:
  assert len(row['variants'])==1
  optimization=json.loads((root/row['key']/'optimization.json').read_text())
  variant=row['variants'][0];report=optimization['dag_reports'][0]
  pr=json.loads((root/row['key']/'variant0/result.json').read_text())
  assert pr['smt']['status']==pr['rtl']['status']=='unsat'
  scoped=has_scoped_one(variant['term']);assert scoped==(row['arm']=='fold_on')
  checks.append({'key':row['key'],'selected_scoped_constant':scoped,**selected_cost(optimization,report)})
 assert len(summary['boundary_checks'])==16 and all(x['pass'] for x in summary['boundary_checks'])
 assert len(summary['definedness'])==3 and all(x['pass'] for x in summary['definedness'])
 assert len(summary['negative_controls'])==3
 for row in summary['negative_controls']:
  pr=json.loads((root/row['kind']/'result.json').read_text())
  assert pr['smt']['status']==pr['rtl']['status']=='sat'
 unique={r['source_sha256']:r for r in audit['synthesis']}
 assert len(unique)==audit['unique_synthesis_calls']==3
 for row in unique.values():
  gates,depth=netlist_cost(root/'synthesis'/Path(row['path']).name/'netlist.json')
  assert (gates,depth)==(row['gates'],row['depth'])
 return {'pass':True,'frozen_git_head':manifest['git_head'],'frozen_sources_verified':len(manifest['files']),'selection_checks':checks,'unique_netlists_recounted':len(unique),'note':'Authored after selection; existing frozen Git sources checked, selected DAG paths and netlist metrics independently recomputed. No new experiment or synthesis.'}

if __name__=='__main__':print(json.dumps(inspect(Path(sys.argv[1])),indent=2))
