"""One frozen, isolated open-tool physical protocol port; no model or GDS claim."""
import os,pathlib,subprocess,time,json,hashlib
from container_cleanup import stop_owned_container
r=pathlib.Path(os.environ['E4_WORK_ROOT']);o=r/'results/fluxbench/physical-v1';data=r/'assets/pdagent/dataset/PlaceReasoner-Bench/bp_fe';image='080c40706b37fb2fece6a61412d17c0e025ee87af82af28e79aa90f5d02a78ac'
assert 'VERIFIED cycles=1000 fetches=333' in (o/'simulate-technology2.log').read_text()
assert not (o/'physical-runs.json').exists()
cpus=','.join(str(x) for x in sorted(os.sched_getaffinity(0))[:4])
base=['taskset','-c',cpus,'podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--pids-limit=128','--memory=8g','--tmpfs=/tmp:rw,noexec,nosuid,size=128m','-e','OMP_NUM_THREADS=4','-e','QT_QPA_PLATFORM=minimal','-v',str(data)+':/data:ro','-v',str(o)+':/out:rw',image,'-no_init','-exit']
lib='read_liberty /data/lib/NangateOpenCellLibrary_typical.lib\n'
rc='''set_thread_count 4
set_wire_rc -signal -layer metal3
set_wire_rc -clock -layer metal5
set_layer_rc -layer metal3 -resistance 0.0035714 -capacitance 0.0888758
set_layer_rc -layer metal5 -resistance 0.0015 -capacitance 0.108964
'''
(o/'port.sdc').write_text('create_clock -name core_clk -period 10 [get_ports clk]\nset_input_delay 0.2 -clock core_clk [get_ports {resetn mem_ready mem_rdata* pcpi_wr pcpi_rd* pcpi_wait pcpi_ready irq*}]\nset_output_delay 0.2 -clock core_clk [all_outputs]\n')
init=lib+'''read_lef /data/lef/NangateOpenCellLibrary.tech.lef
read_lef /data/lef/NangateOpenCellLibrary.macro.mod.lef
read_verilog /out/physical.v
link_design picorv32
read_sdc /out/port.sdc
initialize_floorplan -die_area {0 0 200 200} -core_area {10 10 190 190} -site FreePDK45_38x28_10R_NP_162NW_34O
make_tracks
'''+rc+'''repair_tie_fanout -separation 0 LOGIC0_X1/Z
repair_tie_fanout -separation 0 LOGIC1_X1/Z
place_pins -hor_layers metal3 -ver_layers metal2
write_db /out/floorplan.odb
report_design_area
'''
def load(db):return lib+f'read_db /out/{db}.odb\nread_sdc /out/port.sdc\n'+rc
scripts=[('floorplan',init),('placement',load('floorplan')+'''global_placement -density 0.5
detailed_placement
check_placement -verbose
write_db /out/placement.odb
'''),('cts',load('placement')+'''clock_tree_synthesis -root_buf CLKBUF_X3 -buf_list {CLKBUF_X1 CLKBUF_X2 CLKBUF_X3}
repair_clock_nets
detailed_placement
check_placement -verbose
write_db /out/cts.odb
'''),('routing',load('cts')+'''set_propagated_clock [all_clocks]
set_routing_layers -signal metal2-metal6 -clock metal2-metal6
global_route -guide_file /out/route.guide -congestion_iterations 30
detailed_route -output_drc /out/route.drc -output_maze /out/route.maze.log -bottom_routing_layer metal2 -top_routing_layer metal6 -droute_end_iter 10
write_db /out/route.odb
write_def /out/route.def
write_verilog /out/route.v
'''),('readback',load('route')+'''set_propagated_clock [all_clocks]
estimate_parasitics -placement
check_setup -verbose
report_worst_slack -max
report_worst_slack -min
report_tns
report_design_area
set b [ord::get_db_block]
set placed 0
set clockbuf 0
foreach i [$b getInsts] {
 if {[$i isPlaced]} { incr placed }
 if {[string match "CLKBUF*" [[$i getMaster] getName]]} {incr clockbuf}
}
set wires 0
foreach n [$b getNets] {if {[$n getWire] != "NULL"} {incr wires}}
puts "FACT instances [llength [$b getInsts]]"
puts "FACT placed $placed"
puts "FACT clock_buffers $clockbuf"
puts "FACT routed_nets $wires"
foreach c [all_clocks] {puts "FACT clock [get_name $c] period [get_property $c period]"}
write_db /out/verified.odb
''')]
runs=[]
try:
 for name,s in scripts:
  (o/(name+'.tcl')).write_text(s)
  t=time.monotonic();cmd=base+['/out/'+name+'.tcl']
  container_name='e4-fluxbench-'+name
  image_index=cmd.index(image)
  cmd[image_index:image_index]=['--name',container_name]
  try:
   p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300);text=p.stdout.decode(errors='replace');code=p.returncode;timeout=False
  except subprocess.TimeoutExpired as e:
   text=(e.stdout or b'').decode(errors='replace');code=None;timeout=True
   cleanup=stop_owned_container(container_name,o,'/out/'+name+'.tcl')
   (o/(name+'-cleanup.json')).write_text(json.dumps(cleanup,indent=2)+'\n')
  (o/(name+'.log')).write_text(text);runs.append(dict(stage=name,command=cmd,returncode=code,timeout=timeout,seconds=time.monotonic()-t))
  (o/'physical-runs.json').write_text(json.dumps(runs,indent=2)+'\n')
  if code!=0 or timeout:break
finally:
 artifacts={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in o.iterdir() if p.suffix in ['.odb','.def','.sdc','.tcl','.drc','.guide']}
 (o/'physical-artifacts.json').write_text(json.dumps(artifacts,indent=2)+'\n')
