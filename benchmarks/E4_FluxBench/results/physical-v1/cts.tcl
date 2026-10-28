read_liberty /data/lib/NangateOpenCellLibrary_typical.lib
read_db /out/placement.odb
read_sdc /out/port.sdc
set_thread_count 4
set_wire_rc -signal -layer metal3
set_wire_rc -clock -layer metal5
set_layer_rc -layer metal3 -resistance 0.0035714 -capacitance 0.0888758
set_layer_rc -layer metal5 -resistance 0.0015 -capacitance 0.108964
clock_tree_synthesis -root_buf CLKBUF_X3 -buf_list {CLKBUF_X1 CLKBUF_X2 CLKBUF_X3}
repair_clock_nets
detailed_placement
check_placement -verbose
write_db /out/cts.odb
