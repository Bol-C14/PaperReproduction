"""Real Yosys -> OpenROAD placed PPA. No synthetic objective, no EDA cache."""
import os,json,time,subprocess,hashlib,re,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLATFORM=Path(os.environ.get('ASTROTUNE_PLATFORM','/workspace/scratch/astrotune/platform'))
TOOLS=Path(os.environ.get('ASTROTUNE_TOOLS','/workspace/scratch/astrotune/tools'))
# Local reduced discrete space, not the undisclosed commercial 33-knob list.
SYNTH=[{'fast':f,'delay_ps':d} for f in (False,True) for d in (100,500,2000)]
PLACE=[{'util':u,'density':d} for u in (.25,.35,.45,.55) for d in (.65,.75,.85)]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(cmd,log):
    start=time.monotonic()
    env=dict(os.environ,OMP_NUM_THREADS='1',LD_LIBRARY_PATH=str(TOOLS/'deps')+':'+str(TOOLS/'build/lib'),TCL_LIBRARY=str(TOOLS/'runtime/usr/share/tcl8.5'))
    cmd=[str(TOOLS/'build/bin'/cmd[0])]+cmd[1:]
    r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=180)
    log.write_text(r.stdout+'\nSTDERR\n'+r.stderr)
    if r.returncode: raise RuntimeError(f'{cmd[0]} failed ({r.returncode}): '+r.stdout[-800:]+r.stderr[-400:])
    return time.monotonic()-start

def timing_tcl(top,net,stage,out,area=None,p=0):
    t=f'''read_liberty {PLATFORM}/cells.lib
read_lef {PLATFORM}/tech.lef
read_lef {PLATFORM}/cells.lef
read_verilog {net}
link_design {top}
set_thread_count 1
if {{[llength [get_ports -quiet clk]]}} {{
 create_clock -name core -period 2.0 [get_ports clk]
 set inports {{}}
 foreach port [all_inputs] {{if {{[get_full_name $port] ne "clk"}} {{lappend inports $port}}}}
}} else {{
 create_clock -name core -period 2.0
 set inports [all_inputs]
}}
set_input_delay 0.2 -clock core $inports
set_output_delay 0.2 -clock core [all_outputs]
set_input_transition 0.05 $inports
set_load 0.005 [all_outputs]
'''
    if stage=='place':
        cfg=PLACE[p]; side=max(15,math.sqrt(area/cfg['util'])+4)
        t+=f'''initialize_floorplan -site FreePDK45_38x28_10R_NP_162NW_34O -die_area "0 0 {side+4} {side+4}" -core_area "2 2 {side+2} {side+2}"
make_tracks
place_pins -hor_layers metal3 -ver_layers metal2
source {PLATFORM}/setRC.tcl
global_placement -density {cfg['density']} -overflow 0.2
# Legalize before extracting placement RC.
detailed_placement
check_placement -verbose
estimate_parasitics -placement
write_db {out}/placed.odb
write_def {out}/placed.def
'''
    t+='''report_design_area
report_worst_slack -max
report_power
report_checks -path_delay max -format full_clock_expanded -digits 6
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
set area_dbu 0
foreach inst [$block getInsts] {
 set master [$inst getMaster]
 set area_dbu [expr {$area_dbu + double([$master getWidth])*[$master getHeight]}]
}
puts "AUDIT_AREA [expr {$area_dbu/($dbu*$dbu)}]"
puts "AUDIT_SLACK [sta::worst_slack -max]"
'''
    return t

def parse(log):
    text=log.read_text(); area=float(re.search(r'AUDIT_AREA ([\deE+.-]+)',text)[1]); slack=float(re.search(r'AUDIT_SLACK ([\deE+.-]+)',text)[1])
    # OpenSTA Total row: internal switching leakage total ...; units printed in report.
    row=re.search(r'^Total\s+([\deE+.-]+)\s+([\deE+.-]+)\s+([\deE+.-]+)\s+([\deE+.-]+)',text,re.M)
    if not row: raise RuntimeError('No power Total row')
    power=float(row[4]); assert area>0 and power>0 and math.isfinite(slack)
    return {'area':area,'power':power,'slack':slack}

class EDA:
    def __init__(self,runid):
        self.runid=runid; self.base=ROOT/'work'/runid;self.base.mkdir(parents=True,exist_ok=True);self.records=[]
    def evaluate(self,design,s,p=None,parent=None,label='search'):
        idx=len(self.records); stage='synth' if p is None else 'place'; out=self.base/f'{idx:04d}_{stage}';out.mkdir()
        start=time.monotonic(); rec={'run':self.runid,'id':idx,'design':design['id'],'stage':stage,'s':s,'p':p,'label':label,'out':str(out.relative_to(ROOT)),'status':'failed'}
        try:
            if stage=='synth':
                cfg=SYNTH[s]; net=out/'net.v'; script=f'''read_liberty -lib {PLATFORM}/cells.lib
read_verilog {ROOT/design['rtl']}
synth -top {design['top']} -flatten -noabc
dfflibmap -liberty {PLATFORM}/cells.lib
abc -liberty {PLATFORM}/cells.lib -D {cfg['delay_ps']} {'-fast' if cfg['fast'] else ''}
clean
check -assert
stat -liberty {PLATFORM}/cells.lib
write_verilog -noattr -noexpr {net}
write_json {out}/net.json
'''
                (out/'synth.ys').write_text(script); run(['yosys','-s',str(out/'synth.ys')],out/'yosys.log')
            else:
                assert parent and parent['stage']=='synth' and parent['s']==s and parent['design']==design['id']
                net=ROOT/parent['out']/'net.v';rec['parent_run']=parent['run'];rec['parent_id']=parent['id'];rec['parent_net_sha256']=sha(net)
            (out/'eval.tcl').write_text(timing_tcl(design['top'],net,stage,out,parent['area'] if parent else None,p or 0))
            run(['openroad','-exit',str(out/'eval.tcl')],out/'openroad.log');rec.update(parse(out/'openroad.log'));rec.update(status='ok',net_sha256=sha(net))
            if stage=='place': assert rec['net_sha256']==rec['parent_net_sha256']
        except Exception as e: rec['error']=str(e)
        rec['wall_s']=time.monotonic()-start;self.records.append(rec)
        dest=ROOT/'results'/f'{self.runid}.jsonl'
        with dest.open('a') as f: f.write(json.dumps(rec)+'\n')
        if rec['status']!='ok':raise RuntimeError(rec['error'])
        return rec
