"""Read-only independent checks of stored selection costs and netlist connectivity.

Uses only the standard library, never invokes an optimizer, synthesis or network.
Care predicates are erased from circuit dependency accounting. Reports actual
selected critical paths separately from freely slack model arrival variables.
"""
import hashlib, json, math, subprocess, sys
from pathlib import Path

def intrinsic(node,nodes,selected):
 def literal(i):return json.loads(nodes[node['children'][i]]['op'])
 def bits(c):
  n=nodes[selected[c]];op=n['op']
  if op in ('Ult','Slt','Sge0','And','Not'):return 1
  return json.loads(nodes[n['children'][1 if op=='V' else 0]]['op'])
 op=node['op'];w=bits(node['eclass']);lg=math.ceil(math.log2(max(2,w)))
 if op=='Add':return w,lg+1
 if op=='Mul':
  a,b=[bits(nodes[k]['eclass']) for k in node['children'][1:]]
  return a*b,math.ceil(math.log2(max(2,a)))+math.ceil(math.log2(max(2,b)))+1
 if op=='Shr':
  b=bits(nodes[node['children'][2]]['eclass']);return w*b,b
 if op=='Mux':return w,1
 if op=='Abs':return 2*w,lg+2
 if op=='Neg':return w,lg+1
 if op=='And':return 1,1
 if op in ('Ult','Slt','Sge0'):
  b=bits(nodes[node['children'][0]]['eclass']);return b,math.ceil(math.log2(max(2,b)))+1
 if op in ('V','K','Not','Cut','Ext','Assume'):return 0,0
 raise ValueError(op)

def selected_cost(optimization,report):
 graph=optimization['egraph'];nodes=graph['nodes']
 selected={nodes[k]['eclass']:k for k in report['selected_node_ids']}
 root=next(c for c,d in graph['class_data'].items() if d.get('let')=='$root')
 local={c:intrinsic(nodes[k],nodes,selected) for c,k in selected.items()}
 memo={};visiting=set()
 def delay(c):
  if c in memo:return memo[c]
  if c in visiting:raise AssertionError('Selected cycle')
  visiting.add(c);node=nodes[selected[c]]
  children=[nodes[k]['eclass'] for k in node['children'] if graph['class_data'][nodes[k]['eclass']]['type']=='B']
  if node['op']=='Assume':children=children[:1]
  value=local[c][1]+max((delay(k) for k in children),default=0)
  visiting.remove(c);memo[c]=value;return value
 area=sum(a for a,d in local.values());actual_delay=delay(root)
 assert area==report['area']
 assert actual_delay<=report['delay']<=report['target']
 assert report['lower']==report['upper']
 return {'area':area,'selected_dag_delay':actual_delay,'model_arrival':report['delay'],'target':report['target']}

def netlist_cost(path):
 modules=json.loads(path.read_text())['modules'];assert len(modules)==1
 net=next(iter(modules.values()));cells=net['cells'];driver={}
 for name,cell in cells.items():
  for port,bits in cell['connections'].items():
   if cell['port_directions'][port]=='output':
    for bit in bits:
     assert bit not in driver;driver[bit]=name
 base={b:0 for p in net['ports'].values() if p['direction']=='input' for b in p['bits']}
 base.update({c:0 for c in ['0','1','x','z']});active=set();memo={}
 def level(bit):
  if bit in base:return base[bit]
  name=driver[bit]
  if name in memo:return memo[name]
  assert name not in active;active.add(name);cell=cells[name]
  value=1+max((level(b) for p,bits in cell['connections'].items() if cell['port_directions'][p]=='input' for b in bits),default=0)
  active.remove(name);memo[name]=value;return value
 return len(cells),max(level(b) for p in net['ports'].values() if p['direction']=='output' for b in p['bits'])

def inspect(root):
 manifest=json.loads((root/'manifest.json').read_text())
 for name,digest in manifest['files'].items():
  source=subprocess.check_output(['git','show',manifest['git_head']+':P10/nested_combine_round4/'+name])
  assert hashlib.sha256(source).hexdigest()==digest, name
 summary=json.loads((root/'summary.json').read_text());audit=json.loads((root/'audit.json').read_text())
 assert summary['pass'] and audit['pass'];assert len(summary['rows'])==18
 checks=[]
 for row in summary['rows']:
  optimization=json.loads((root/row['key']/'optimization.json').read_text())
  assert row['pass'] and len(row['variants'])==2
  for i,(variant,report) in enumerate(zip(row['variants'],optimization['dag_reports'])):
   assert variant['proof']['pass']
   checks.append({'key':row['key'],'variant':i,**selected_cost(optimization,report)})
 unique={r['source_sha256']:r for r in audit['synthesis']}
 assert len(unique)==audit['unique_synthesis_calls']<=42
 for r in unique.values():
  path=root/'synthesis'/Path(r['path']).name/'netlist.json'
  gates,depth=netlist_cost(path);assert (gates,depth)==(r['gates'],r['depth'])
 assert len(summary['negative_controls'])==3 and all(r['pass'] for r in summary['negative_controls'])
 assert len(summary['definedness'])==8 and all(r['pass'] for r in summary['definedness'])
 return {'pass':True,'frozen_git_head':manifest['git_head'],'frozen_sources_verified':len(manifest['files']),'selected_dag_checks':checks,'unique_netlist_recounts':len(unique),'positive_smt_rtl_pairs':36,'negative_smt_rtl_pairs':3,'partial_semantics_obligations':8,'note':'Post-selection independent read-only audit, no reruns or new selection. Model arrival may include slack; selected_dag_delay is recomputed from chosen dependencies.'}

if __name__=='__main__':
 print(json.dumps(inspect(Path(sys.argv[1])),indent=2))
