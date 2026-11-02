"""Local-copy boundary controls, no EDA. Outputs evidence JSON."""
from pathlib import Path
import json,tempfile
from identity_v2 import canonical_file
P=Path(__file__).resolve().parents[1];D=P/'logs/physical-only-round3/A1_noop'
def short(s):
 lines=s.splitlines(keepends=True);out=[];skip=False
 for x in lines:
  if x.startswith('// Command     :'):
   out.append('// Command     : write_verilog -force -mode funcsim snapshot_funcsim.v\n');skip=True
  elif skip and x.startswith('//               /home/'):
   skip=False
  else:out.append(x)
 return ''.join(out)
a=short((D/'before_funcsim.v').read_text());b=short((D/'after_funcsim.v').read_text())
x=(D/'before_constraints.xdc').read_text();x='\n'.join('# Command Used: write_xdc -force snapshot_constraints.xdc' if z.startswith('# Command Used:') else z for z in x.split('\n'))
cases=[('short_name_before_after_Date_only',a,b,'.v',True),('timescale_change',a,b.replace('`timescale 1 ps / 1 ps','`timescale 1 ns / 1 ps',1),'.v',False),('LUT_INIT_change',a,b.replace(".INIT(64'hEAFFFFFFEA000000)",".INIT(64'hEAFFFFFFEA000001)",1),'.v',False),('semantic_comment_in_body',a,b.replace('module DataCache\n','// synthesis translate_off\nmodule DataCache\n',1),'.v',False),('new_directive_before_timescale',a,b.replace('`timescale','`define ALTERED 1\n`timescale',1),'.v',False),('wire_added',a,b.replace('module DataCache\n','wire unexpected;\nmodule DataCache\n',1),'.v',False),('XDC_identical',x,x,'.xdc',True),('clock_period_change',x,x.replace('create_clock -period 1.570','create_clock -period 1.580',1),'.xdc',False),('XDC_comment_change',x,x+'\n# unexpected extra text\n','.xdc',False),('old_wrapped_metadata_rejected',a,(D/'after_funcsim.v').read_text(),'.v',False)]
rows=[]
with tempfile.TemporaryDirectory(prefix='rq1-identity-v2-') as tmp:
 for name,left,right,ext,expected in cases:
  if not expected:assert left!=right
  p=Path(tmp)/('left'+ext);q=Path(tmp)/('right'+ext);p.write_text(left);q.write_text(right)
  try:accepted=canonical_file(p)==canonical_file(q);error=None
  except (ValueError,StopIteration) as e:accepted=False;error=str(e)
  rows.append({'case':name,'expected_accept':expected,'accepted':accepted,'error':error})
assert all(r['expected_accept']==r['accepted'] for r in rows),rows
(P/'IDENTITY_V2_CONTROLS.json').write_text(json.dumps({'scope':'synthetic_short_export_headers_on_copied_real_HDL_and_XDC; no_EDA','results':rows},indent=2)+'\n')
print('passed',len(rows),'identity-v2 boundary controls')
