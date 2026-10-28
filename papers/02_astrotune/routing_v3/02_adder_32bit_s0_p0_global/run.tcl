read_liberty /workspace/scratch/astrotune/platform/cells.lib
read_db /workspace/PaperReproduction/papers/02_astrotune/work/adder_32bit_ast_gp_all_0/0001_place/placed.odb
set_thread_count 1
create_clock -name core -period 2.0
set_input_delay 0.2 -clock core [all_inputs]
set_output_delay 0.2 -clock core [all_outputs]
set_input_transition 0.05 [all_inputs]
set_load 0.005 [all_outputs]
source /workspace/scratch/astrotune/platform/setRC.tcl
insert_tiecells LOGIC0_X1/Z
insert_tiecells LOGIC1_X1/Z
detailed_placement
check_placement -verbose
set_routing_layers -signal metal2-metal6 -clock metal2-metal6
set_global_routing_layer_adjustment metal2-metal6 0.30
global_route -guide_file /workspace/PaperReproduction/papers/02_astrotune/routing_v3/02_adder_32bit_s0_p0_global/route.guide -verbose
estimate_parasitics -global_routing
write_db /workspace/PaperReproduction/papers/02_astrotune/routing_v3/02_adder_32bit_s0_p0_global/routed.odb
write_def /workspace/PaperReproduction/papers/02_astrotune/routing_v3/02_adder_32bit_s0_p0_global/routed.def
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
