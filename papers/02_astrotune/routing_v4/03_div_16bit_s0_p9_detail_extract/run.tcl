read_liberty /workspace/scratch/astrotune/platform/cells.lib
read_db /workspace/PaperReproduction/papers/02_astrotune/routing_v4/02_div_16bit_s0_p9_global/routed.odb
set_thread_count 1
create_clock -name core -period 2.0
set_input_delay 0.2 -clock core [all_inputs]
set_output_delay 0.2 -clock core [all_outputs]
set_input_transition 0.05 [all_inputs]
set_load 0.005 [all_outputs]
source /workspace/scratch/astrotune/platform/setRC.tcl
detailed_route -output_drc /workspace/PaperReproduction/papers/02_astrotune/routing_v4/03_div_16bit_s0_p9_detail_extract/drc.rpt -output_maze /workspace/PaperReproduction/papers/02_astrotune/routing_v4/03_div_16bit_s0_p9_detail_extract/maze.log -bottom_routing_layer metal2 -top_routing_layer metal6 -or_seed 0
estimate_parasitics -global_routing
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file /workspace/scratch/astrotune/platform/rcx_patterns.rules
write_spef /workspace/PaperReproduction/papers/02_astrotune/routing_v4/03_div_16bit_s0_p9_detail_extract/routed.spef
read_spef /workspace/PaperReproduction/papers/02_astrotune/routing_v4/03_div_16bit_s0_p9_detail_extract/routed.spef
write_db /workspace/PaperReproduction/papers/02_astrotune/routing_v4/03_div_16bit_s0_p9_detail_extract/routed.odb
write_def /workspace/PaperReproduction/papers/02_astrotune/routing_v4/03_div_16bit_s0_p9_detail_extract/routed.def
report_design_area
report_worst_slack -max
report_power
report_checks -path_delay max -format full_clock_expanded -digits 6
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
set area_dbu 0
foreach inst [$block getInsts] {
 set master [$inst getMaster]
 set area_dbu [expr {$area_dbu+double([$master getWidth])*[$master getHeight]}]
}
puts "AUDIT_AREA [expr {$area_dbu/($dbu*$dbu)}]"
puts "AUDIT_SLACK [sta::worst_slack -max]"
