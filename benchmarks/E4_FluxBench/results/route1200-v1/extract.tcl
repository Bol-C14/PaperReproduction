read_liberty /data/lib/NangateOpenCellLibrary_typical.lib
read_db /out/route.odb
read_sdc /out/port.sdc
set_thread_count 4
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file /assets/rcx_patterns.rules
write_spef /out/extracted.spef
report_worst_slack -max
report_worst_slack -min
report_tns
report_checks -path_delay max -group_count 1
