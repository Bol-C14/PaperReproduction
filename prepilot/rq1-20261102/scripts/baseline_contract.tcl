set_param general.maxThreads 2
set src [lindex $argv 0]
set out [lindex $argv 1]
open_checkpoint $src
help phys_opt_design
help route_design
foreach tag {original serialized} {
 if {$tag eq "serialized"} {
  close_design
  open_checkpoint [file join $out serialized.dcp]
 }
 report_timing_summary -max_paths 5 -file [file join $out ${tag}_timing.rpt]
 report_route_status -file [file join $out ${tag}_route.rpt]
 report_drc -file [file join $out ${tag}_drc.rpt]
 write_verilog -force -mode funcsim [file join $out ${tag}_funcsim.v]
 write_xdc -force [file join $out ${tag}_constraints.xdc]
 set fp [open [file join $out ${tag}_ports.tsv] w]
 foreach p [lsort [get_ports]] {puts $fp "$p\t[get_property DIRECTION [get_ports $p]]"}
 close $fp
 if {$tag eq "original"} {write_checkpoint -force [file join $out serialized.dcp]}
 puts "RQ1_CONTRACT_STAGE_COMPLETE=$tag"
}
close_design
exit
