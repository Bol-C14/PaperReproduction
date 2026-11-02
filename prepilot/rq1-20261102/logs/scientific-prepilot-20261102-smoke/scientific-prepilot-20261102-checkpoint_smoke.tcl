# Bounded real-DCP no-op round trip. No optimization or model requests.
set_param general.maxThreads 2
set src [lindex $argv 0]
set out [lindex $argv 1]
set t0 [clock milliseconds]
open_checkpoint $src
puts "PREPILOT_READ_OK cells=[llength [get_cells -hierarchical]] nets=[llength [get_nets -hierarchical]]"
report_route_status -file [file join $out route_status.rpt]
report_timing_summary -max_paths 3 -file [file join $out timing_summary.rpt]
report_utilization -file [file join $out utilization.rpt]
write_checkpoint -force [file join $out noop.dcp]
close_design
open_checkpoint [file join $out noop.dcp]
puts "PREPILOT_REOPEN_OK cells=[llength [get_cells -hierarchical]] nets=[llength [get_nets -hierarchical]]"
puts "PREPILOT_ELAPSED_MS=[expr {[clock milliseconds]-$t0}]"
close_design
exit
