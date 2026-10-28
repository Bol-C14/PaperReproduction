read_liberty /data/lib/NangateOpenCellLibrary_typical.lib
read_db /out/cts.odb
read_sdc /out/port.sdc
set_thread_count 4
set_wire_rc -signal -layer metal3
set_wire_rc -clock -layer metal5
set_layer_rc -layer metal3 -resistance 0.0035714 -capacitance 0.0888758
set_layer_rc -layer metal5 -resistance 0.0015 -capacitance 0.108964
set_propagated_clock [all_clocks]
set_routing_layers -signal metal2-metal6 -clock metal2-metal6
global_route -guide_file /out/route.guide -congestion_iterations 30
detailed_route -output_drc /out/route.drc -output_maze /out/route.maze.log -bottom_routing_layer metal2 -top_routing_layer metal6 -droute_end_iter 10
write_db /out/route.odb
write_def /out/route.def
write_verilog /out/route.v
