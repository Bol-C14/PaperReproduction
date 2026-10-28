import os,pathlib,subprocess,json,time,hashlib
r=pathlib.Path(os.environ['E4_WORK_ROOT']);o=r/'results/fluxbench/physical-v1';data=r/'assets/pdagent/dataset/PlaceReasoner-Bench/bp_fe';db='route' if (o/'route.odb').exists() else 'cts'
# This validator must be invoked after the bounded physical process has ended.
s=f'''read_liberty /data/lib/NangateOpenCellLibrary_typical.lib
read_db /out/{db}.odb
read_sdc /out/port.sdc
set_thread_count 4
set_layer_rc -layer metal3 -resistance 0.0035714 -capacitance 0.0888758
set_layer_rc -layer metal5 -resistance 0.0015 -capacitance 0.108964
set_wire_rc -signal -layer metal3
set_wire_rc -clock -layer metal5
set_propagated_clock [all_clocks]
estimate_parasitics -placement
check_setup -verbose
report_worst_slack -max
report_worst_slack -min
report_tns
report_design_area
set b [ord::get_db_block]
set placed 0
set clockbuf 0
foreach i [$b getInsts] {{
 if {{[$i isPlaced]}} {{incr placed}}
 if {{[string match "CLKBUF*" [[$i getMaster] getName]]}} {{incr clockbuf}}
}}
set wires 0
set unwired 0
foreach n [$b getNets] {{
 if {{[$n getWire] != "NULL"}} {{incr wires}}
 if {{[$n getSigType] != "POWER" && [$n getSigType] != "GROUND" && [expr {{[llength [$n getITerms]]+[llength [$n getBTerms]]}}]>1 && [$n getWire] == "NULL"}} {{incr unwired}}
}}
puts "FACT instances [llength [$b getInsts]]"
puts "FACT placed $placed"
puts "FACT clock_buffers $clockbuf"
puts "FACT routed_nets $wires"
puts "FACT multi_terminal_unwired $unwired"
foreach c [all_clocks] {{puts "FACT clock [get_name $c] period [get_property $c period]"}}
write_db /out/independent-{db}.odb
write_def /out/independent-{db}.def
write_verilog /out/independent-{db}.v
'''
(o/'independent-readback.tcl').write_text(s)
cpus=','.join(str(x) for x in sorted(os.sched_getaffinity(0))[:4]);image='080c40706b37fb2fece6a61412d17c0e025ee87af82af28e79aa90f5d02a78ac'
cmd=['taskset','-c',cpus,'podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--pids-limit=128','--memory=8g','--tmpfs=/tmp:rw,noexec,nosuid,size=128m','-e','OMP_NUM_THREADS=4','-e','QT_QPA_PLATFORM=minimal','-v',str(data)+':/data:ro','-v',str(o)+':/out:rw',image,'-no_init','-exit','/out/independent-readback.tcl']
t=time.monotonic();p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(o/'independent-readback.log').write_bytes(p.stdout)
facts=[l for l in p.stdout.decode(errors='replace').splitlines() if l.startswith('FACT ')]
(o/'independent-readback.json').write_text(json.dumps(dict(checkpoint=db,command=cmd,returncode=p.returncode,seconds=time.monotonic()-t,facts=facts,timing='placement-estimated only; not extracted/signoff',checkpoint_sha256=hashlib.sha256((o/(db+'.odb')).read_bytes()).hexdigest(),constraint_sha256=hashlib.sha256((o/'port.sdc').read_bytes()).hexdigest()),indent=2)+'\n');assert p.returncode==0
