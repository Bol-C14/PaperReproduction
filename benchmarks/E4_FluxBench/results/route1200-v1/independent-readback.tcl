read_liberty /data/lib/NangateOpenCellLibrary_typical.lib
read_db /out/route.odb
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
foreach i [$b getInsts] {
 if {[$i isPlaced]} {incr placed}
 if {[string match "CLKBUF*" [[$i getMaster] getName]]} {incr clockbuf}
}
set wires 0
set unwired 0
foreach n [$b getNets] {
 if {[$n getWire] != "NULL"} {incr wires}
 if {[$n getSigType] != "POWER" && [$n getSigType] != "GROUND" && [expr {[llength [$n getITerms]]+[llength [$n getBTerms]]}]>1 && [$n getWire] == "NULL"} {incr unwired}
}
puts "FACT instances [llength [$b getInsts]]"
puts "FACT placed $placed"
puts "FACT clock_buffers $clockbuf"
puts "FACT routed_nets $wires"
puts "FACT multi_terminal_unwired $unwired"
foreach c [all_clocks] {puts "FACT clock [get_name $c] period [get_property $c period]"}
write_db /out/independent-route.odb
write_def /out/independent-route.def
write_verilog /out/independent-route.v
