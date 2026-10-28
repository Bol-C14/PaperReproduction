"""Bounded actual OpenROAD routing, no models/search/metric-cache pretending EDA."""
import json,time,hashlib,subprocess,os,sys,re
from pathlib import Path
from eda import ROOT,TOOLS,PLATFORM,sha,parse,PLACE
BASE=ROOT/'routing_v3';BASE.mkdir(exist_ok=True)

def find_parent(design,s,p):
 for f in sorted((ROOT/'results').glob('*.jsonl')):
  for l in f.read_text().splitlines():
   r=json.loads(l)
   if r['status']=='ok' and r['design']==design and r['stage']=='place' and r['s']==s and r['p']==p and (ROOT/r['out']/'placed.odb').exists():return r
 raise RuntimeError('missing real parent')

def metric_tcl():
 return '''report_design_area
report_worst_slack -max
report_power
report_checks -path_delay max -format full_clock_expanded -digits 6
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
set area_dbu 0
foreach inst [$block getInsts] {
 set master [$inst getMaster]
 set area_dbu [expr {$area_dbu+double([$master getWidth])*[$master getHeight]}]
}
puts "AUDIT_AREA [expr {$area_dbu/($dbu*$dbu)}]"
puts "AUDIT_SLACK [sta::worst_slack -max]"
'''

def attempt(design,s,p,stage='global',input_db=None,seed=0,timeout_s=180):
 ledger=BASE/'attempts.jsonl';old=[json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else []
 assert len(old)<(15 if stage=='spef_audit' else 12) and sum(r['wall_s'] for r in old)<1200,'frozen routing budget exhausted'
 parent=find_parent(design,s,p);idx=len(old);out=BASE/f'{idx:02d}_{design}_s{s}_p{p}_{stage}';out.mkdir();db=Path(input_db) if input_db else ROOT/parent['out']/'placed.odb'
 t=f'''read_liberty {PLATFORM}/cells.lib
read_db {db}
set_thread_count 1
create_clock -name core -period 2.0
set_input_delay 0.2 -clock core [all_inputs]
set_output_delay 0.2 -clock core [all_outputs]
set_input_transition 0.05 [all_inputs]
set_load 0.005 [all_outputs]
source {PLATFORM}/setRC.tcl
'''
 if stage=='global':
  t+=f'''insert_tiecells LOGIC0_X1/Z
insert_tiecells LOGIC1_X1/Z
global_placement -density {PLACE[p]["density"]} -overflow 0.2
detailed_placement
check_placement -verbose
estimate_parasitics -placement
puts EARLY_BEGIN
{metric_tcl()}
puts EARLY_END
set_routing_layers -signal metal2-metal6 -clock metal2-metal6
set_global_routing_layer_adjustment metal2-metal6 0.30
global_route -guide_file {out}/route.guide -verbose
estimate_parasitics -global_routing
'''
 elif stage in ('detail','detail_extract'):
  t+=f'''detailed_route -output_drc {out}/drc.rpt -output_maze {out}/maze.log -bottom_routing_layer metal2 -top_routing_layer metal6 -or_seed {seed}
estimate_parasitics -global_routing
'''
 elif stage=='extract':pass
 elif stage=='spef_audit':t+=f'read_spef {db.parent}/routed.spef\n'
 elif stage=='early_audit':t+='estimate_parasitics -placement\n'
 else:raise ValueError(stage)
 if stage in ('extract','detail_extract'):
  t+=f'''define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file {PLATFORM}/rcx_patterns.rules
write_spef {out}/routed.spef
read_spef {out}/routed.spef
'''

 t+=f'write_db {out}/routed.odb\nwrite_def {out}/routed.def\n'+metric_tcl();(out/'run.tcl').write_text(t)
 env=dict(os.environ,OMP_NUM_THREADS='1',LD_LIBRARY_PATH=str(TOOLS/'deps')+':'+str(TOOLS/'build/lib'),TCL_LIBRARY=str(TOOLS/'runtime/usr/share/tcl8.5'))
 cmd=[str(TOOLS/'build/bin/openroad'),'-exit',str(out/'run.tcl')];start=time.monotonic();rec={'attempt':idx,'design':design,'s':s,'p':p,'stage':stage,'seed':seed,'timeout_s':timeout_s,'parent_run':parent['run'],'parent_id':parent['id'],'parent_net_sha256':parent['net_sha256'],'parent_placement':parent,'input_db':str(db),'input_db_sha256':sha(db),'command':cmd,'status':'failed','rc_method':'explicit SPEF readback of detailed-wire OpenRCX' if stage=='spef_audit' else 'placement-estimated RC on repaired implementation' if stage=='early_audit' else 'OpenRCX detailed-wire extraction (not signoff)' if stage in ('extract','detail_extract') else 'global-routing estimate (not signoff)','llm_calls':0}
 try:
  r=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=timeout_s);(out/'tool.log').write_text(r.stdout+'\nSTDERR\n'+r.stderr);rec['exit']=r.returncode
  if r.returncode:raise RuntimeError(r.stdout[-1000:]+r.stderr[-500:])
  logtext=(out/'tool.log').read_text()
  if 'EARLY_END' in logtext:
   (out/'early_metrics.log').write_text(logtext.split('EARLY_BEGIN')[1].split('EARLY_END')[0]);rec['early_metrics']=parse(out/'early_metrics.log')
   (out/'final_metrics.log').write_text(logtext.split('EARLY_END',1)[1]);metrics=out/'final_metrics.log'
  else:metrics=out/'tool.log'
  rec.update(parse(metrics))
  if stage=='global':
   assert 'Routed nets:' in logtext and (out/'route.guide').stat().st_size>0
   assert re.search(r'^Total\s+\d+\s+\d+\s+[\d.]+%\s+0 /\s*0 /\s*0',logtext,re.M),'nonzero global overflow'
  if stage in ('detail','detail_extract'):
   assert (out/'drc.rpt').exists() and not (out/'drc.rpt').read_text().strip(),'nonempty/missing DRC report'
   assert re.findall(r'Number of violations = (\d+)',logtext)[-1]=='0'
   assert 'Complete detail routing.' in logtext
  if stage in ('extract','detail_extract'):assert '*RES' in (out/'routed.spef').read_text()
  rec['output_db_sha256']=sha(out/'routed.odb');rec['output_db']=str(out/'routed.odb');rec['status']='ok'
  if stage in ('detail','detail_extract'):rec['drc_report']=(out/'drc.rpt').read_text() if (out/'drc.rpt').exists() else None
 except subprocess.TimeoutExpired as e:
  def text(x):return x.decode(errors='replace') if isinstance(x,bytes) else (x or '')
  (out/'tool.log').write_text(text(e.stdout)+'\n'+text(e.stderr));rec['error']='timeout'+str(timeout_s)+'seconds'
 except Exception as e:rec['error']=str(e)
 rec['wall_s']=time.monotonic()-start;rec['out']=str(out.relative_to(ROOT))
 with ledger.open('a') as f:f.write(json.dumps(rec)+'\n')
 print(json.dumps(rec,indent=2));return rec
if __name__=='__main__':attempt(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4] if len(sys.argv)>4 else 'global',sys.argv[5] if len(sys.argv)>5 else None)
