read_liberty /workspace/scratch/astrotune/platform/cells.lib
read_lef /workspace/scratch/astrotune/platform/tech.lef
read_lef /workspace/scratch/astrotune/platform/cells.lef
read_verilog /workspace/PaperReproduction/papers/02_astrotune/work/multi_pipe_8bit_gp_single_0/0000_synth/net.v
link_design verified_multi_pipe_8bit
set_thread_count 1
if {[llength [get_ports -quiet clk]]} {
 create_clock -name core -period 2.0 [get_ports clk]
 set inports {}
 foreach port [all_inputs] {if {[get_full_name $port] ne "clk"} {lappend inports $port}}
} else {
 create_clock -name core -period 2.0
 set inports [all_inputs]
}
set_input_delay 0.2 -clock core $inports
set_output_delay 0.2 -clock core [all_outputs]
set_input_transition 0.05 $inports
set_load 0.005 [all_outputs]
initialize_floorplan -site FreePDK45_38x28_10R_NP_162NW_34O -die_area "0 0 67.96932549228814 67.96932549228814" -core_area "2 2 65.96932549228814 65.96932549228814"
make_tracks
place_pins -hor_layers metal3 -ver_layers metal2
source /workspace/scratch/astrotune/platform/setRC.tcl
global_placement -density 0.65 -overflow 0.2
# Legalize before extracting placement RC.
detailed_placement
check_placement -verbose
estimate_parasitics -placement
write_db /workspace/PaperReproduction/papers/02_astrotune/work/multi_pipe_8bit_gp_single_0/0001_place/placed.odb
write_def /workspace/PaperReproduction/papers/02_astrotune/work/multi_pipe_8bit_gp_single_0/0001_place/placed.def
report_design_area
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
