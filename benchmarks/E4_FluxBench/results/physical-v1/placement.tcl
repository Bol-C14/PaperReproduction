read_liberty /data/lib/NangateOpenCellLibrary_typical.lib
read_db /out/floorplan.odb
read_sdc /out/port.sdc
set_thread_count 4
set_wire_rc -signal -layer metal3
set_wire_rc -clock -layer metal5
set_layer_rc -layer metal3 -resistance 0.0035714 -capacitance 0.0888758
set_layer_rc -layer metal5 -resistance 0.0015 -capacitance 0.108964
global_placement -density 0.5
detailed_placement
check_placement -verbose
write_db /out/placement.odb
