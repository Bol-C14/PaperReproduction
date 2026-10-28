#!/usr/bin/env python3
"""Extract all fanout connections of one existing public AES data net.
The logical cut is real; geometry, timing boundaries and downstream loads are local assumptions.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
from pilot import ROOT, fixture
p=argparse.ArgumentParser();p.add_argument('--netlist',required=True);a=p.parse_args()
path=Path(a.netlist);data=path.read_bytes();s=data.decode();net='_08638_';loads=[];driver=None
for m in re.finditer(r'(\w+_ASAP7_75t_R)\s+(\w+)\s*\((.*?)\);',s,re.S):
 cell,inst,body=m.groups()
 for pin,wire in re.findall(r'\.(\w+)\s*\(\s*([^()]+?)\s*\)',body):
  if wire==net:
   if pin=='Y':
    assert driver is None;driver={'cell':cell,'instance':inst,'pin':pin}
   else:loads.append({'cell':cell,'instance':inst,'pin':pin})
assert len(loads)==10 and driver['cell']=='BUFx2_ASAP7_75t_R'
assert all(x['cell']==driver['cell'] and x['pin']=='A' for x in loads)
f=fixture('spread');f['name']='aes_cut';f['kind']='actual AES net connectivity; synthetic geometry and cut timing constraints';f['sinks']=f['sinks'][:10]
f['source']={'url':'https://github.com/The-OpenROAD-Project/OpenSTA/blob/384b539085c54eef46cbaa02e2e17d2b983247e5/test/asap7/designs/aes.v','sha256':hashlib.sha256(data).hexdigest(),'net':net,'driver':driver,'all_loads':loads,'scope':'complete original fanout retained; other nets and downstream logic cut; original placement/timing not provided'}
(ROOT/'config'/'aes_cut.json').write_text(json.dumps(f,indent=2)+'\n');print(json.dumps(f['source'],indent=2))
