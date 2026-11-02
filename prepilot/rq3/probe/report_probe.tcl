# Read-only observations; no optimization, route, write_checkpoint or model.
set_param general.maxThreads 2
set out [lindex $argv 0]
set original [lindex $argv 1]
set updated [lindex $argv 2]
set ledger [open [file join $out tool_events.tsv] w]
puts $ledger "state\tphase\tquery\tstatus\telapsed_ms\tfile"
proc observe {state phase query command filename} {
    global ledger
    set begin [clock milliseconds]
    set status [catch {uplevel 1 $command} result]
    puts $ledger "$state\t$phase\t$query\t$status\t[expr {[clock milliseconds]-$begin}]\t$filename"
    flush $ledger
    if {$status} {puts "RQ3_QUERY_ERROR $state $query $result"}
}
foreach state {original updated} src [list $original $updated] {
    set begin [clock milliseconds]
    open_checkpoint $src
    puts $ledger "$state\tload\topen_checkpoint\t0\t[expr {[clock milliseconds]-$begin}]\t-"
    puts "RQ3_OPEN_OK $state"
    # Keep baseline reports, and repeat generation to expose warm-engine effects.
    foreach phase {first warm_regenerate} {
        set base [file join $out ${state}_${phase}]
        observe $state $phase timing [list report_timing_summary -file ${base}_timing.rpt] ${base}_timing.rpt
        observe $state $phase fanout [list report_high_fanout_nets -max_nets 20 -file ${base}_fanout.rpt] ${base}_fanout.rpt
        observe $state $phase paths [list report_timing -delay_type max -max_paths 50 -nworst 1 -file ${base}_paths.rpt] ${base}_paths.rpt
        observe $state $phase complexity [list report_design_analysis -complexity -file ${base}_complexity.rpt] ${base}_complexity.rpt
        observe $state $phase congestion [list report_design_analysis -congestion -file ${base}_congestion.rpt] ${base}_congestion.rpt
    }
    close_design
}
close $ledger
exit
