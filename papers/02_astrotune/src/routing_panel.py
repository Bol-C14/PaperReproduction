"""Four frozen candidates;<=8 actual calls; no model/API/search/retry."""
import json,hashlib
from routing_round import attempt,find_parent
from eda import ROOT,sha
B=ROOT/'routing_v4';B.mkdir(exist_ok=True)
panel=[('div_16bit',0,0),('div_16bit',0,9),('adder_32bit',3,0),('adder_32bit',3,9)]
inputs=[]
for d,s,p in panel:
 r=find_parent(d,s,p);inputs.append({'design':d,'s':s,'p':p,'source':r,'input_db_sha256':sha(ROOT/r['out']/'placed.odb')})
(B/'input_panel.json').write_text(json.dumps(inputs,indent=2))
assert find_parent('adder_32bit',3,0)['net_sha256']!=find_parent('adder_32bit',0,0)['net_sha256']
for i,(d,s,p) in enumerate(panel):
 g=attempt(d,s,p,'global',timeout_s=60,base=B,max_calls=8)
 if g['status']!='ok':
  if i==0:break
  continue
 r=attempt(d,s,p,'detail_extract',g['output_db'],timeout_s=120,base=B,max_calls=8)
 if i==0 and r['status']!='ok':break
