set_param general.maxThreads 2
if {$argc != 3} {error "Expected input output_dir noop|routing_opt"}
lassign $argv src out action
if {$action ni {noop routing_opt}} {error "Unregistered action"}
open_checkpoint $src
proc capture {out tag} {
 report_timing_summary -max_paths 5 -file [file join $out ${tag}_timing.rpt]
 write_verilog -force -mode funcsim [file join $out ${tag}_funcsim.v]
 write_xdc -force [file join $out ${tag}_constraints.xdc]
 set c [get_clocks clk_fpl26contest]
 if {[llength $c] != 1} {error "Missing or ambiguous contest clock"}
 set p [get_timing_paths -setup -max_paths 1 -to $c]
 if {[llength $p] != 1} {error "No contest setup path"}
 set f [open [file join $out ${tag}_contest.tsv] w]
 puts $f "period_ns\t[get_property PERIOD $c]"
 puts $f "wns_ns\t[get_property SLACK $p]"
 close $f
}
capture $out before
puts "RQ1_PHYSICAL_ACTION=$action"
set t [clock milliseconds]
if {$action eq "routing_opt"} {phys_opt_design -routing_opt}
puts "RQ1_PHYSOPT_MS=[expr {[clock milliseconds]-$t}]"
set t [clock milliseconds]
route_design -no_psir
puts "RQ1_ROUTE_MS=[expr {[clock milliseconds]-$t}]"
capture $out after
report_route_status -file [file join $out route.rpt]
report_drc -file [file join $out drc.rpt]
write_checkpoint -force [file join $out output.dcp]
puts "RQ1_PHYSICAL_ARM_COMPLETE=$action"
close_design
exit
