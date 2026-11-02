# STAGED ONLY: no invocation authorized. Separate process for each candidate.
set_param general.maxThreads 2
if {$argc != 3} { error "Expected input.dcp output_dir path_id" }
lassign $argv src out path_id
if {$path_id ni {RouteNoPSIR RouteNoPSIRTNS}} { error "Unregistered path" }
file mkdir $out
puts [help route_design]
open_checkpoint $src
write_edif -force [file join $out before.edf]
write_xdc -force [file join $out before.xdc]
report_timing_summary -max_paths 3 -file [file join $out before_timing.rpt]
if {$path_id eq "RouteNoPSIR"} {
    route_design -no_psir
} else {
    route_design -no_psir -tns_cleanup
}
report_route_status -file [file join $out route.rpt]
report_drc -file [file join $out drc.rpt]
report_timing_summary -max_paths 3 -file [file join $out timing.rpt]
report_utilization -file [file join $out utilization.rpt]
write_edif -force [file join $out after.edf]
write_xdc -force [file join $out after.xdc]
write_checkpoint -force [file join $out output.dcp]
close_design
exit
