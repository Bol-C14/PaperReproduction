set_param general.maxThreads 2
set src [lindex $argv 0]
set out [lindex $argv 1]
set action [lindex $argv 2]
open_checkpoint $src
puts "RQ1_ACTION=$action"
puts [help phys_opt_design]
puts [help route_design]
set t [clock milliseconds]
if {$action ne "noop"} {phys_opt_design -directive $action}
puts "RQ1_PHYSOPT_MS=[expr {[clock milliseconds]-$t}]"
# Identical completion operation in every arm, including the no-edit baseline.
set t [clock milliseconds]
route_design
puts "RQ1_ROUTE_MS=[expr {[clock milliseconds]-$t}]"
report_timing_summary -max_paths 5 -file [file join $out timing.rpt]
report_route_status -file [file join $out route.rpt]
report_drc -file [file join $out drc.rpt]
write_verilog -force -mode funcsim [file join $out funcsim.v]
write_xdc -force [file join $out constraints.xdc]
write_checkpoint -force [file join $out output.dcp]
puts "RQ1_ARM_COMPLETE=$action"
close_design
exit
