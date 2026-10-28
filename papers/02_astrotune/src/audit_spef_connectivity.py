"""Offline terminal-to-terminal resistor-graph connectivity audit of extracted SPEF.
Not LVS/DRC; no EDA/model/API calls. Preserve uncertain zero-R cases explicitly.
"""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'routing_v4';rows=[]
for f in sorted(B.glob('*detail_extract/routed.spef')):
 nets=[];section=None;net=None
 for line in f.read_text().splitlines():
  x=line.split()
  if not x:continue
  if x[0]=='*D_NET':net={'net':x[1],'terminals':[],'edges':[]};nets.append(net);section=None
  elif x[0] in ('*CONN','*CAP','*RES','*END'):section=x[0]
  elif net is not None and section=='*CONN' and x[0] in ('*P','*I'):net['terminals'].append(x[1])
  elif net is not None and section=='*RES' and x[0].isdigit():net['edges'].append((x[1],x[2]))
 bad=[];checked=0
 for n in nets:
  if len(n['terminals'])<2:continue
  checked+=1;parent={}
  def find(x):
   parent.setdefault(x,x)
   if parent[x]!=x:parent[x]=find(parent[x])
   return parent[x]
  for a,b in n['edges']:parent[find(a)]=find(b)
  groups={find(x) for x in n['terminals']}
  if len(groups)!=1:bad.append({'net':n['net'],'terminal_count':len(n['terminals']),'components':len(groups),'terminal_examples':n['terminals'][:6],'resistor_edges':len(n['edges'])})
 rows.append({'spef':str(f.relative_to(ROOT)),'nets':len(nets),'multi_terminal_nets_checked':checked,'disconnected_terminal_graph_nets':len(bad),'examples':bad[:20]})
(B/'spef_connectivity.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
