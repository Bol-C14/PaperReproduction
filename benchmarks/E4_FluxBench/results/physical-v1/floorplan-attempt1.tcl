read_liberty /data/lib/NangateOpenCellLibrary_typical.lib
read_lef /data/lef/NangateOpenCellLibrary.tech.lef
read_lef /data/lef/NangateOpenCellLibrary.macro.mod.lef
read_verilog /out/physical.v
link_design picorv32
read_sdc /out/port.sdc
initialize_floorplan -die_area {0 0 200 200} -core_area {10 10 190 190} -site FreePDK45_38x28_10R_NP_162NW_34O
make_tracks
set_thread_count 4
set_wire_rc -signal -layer metal3
set_wire_rc -clock -layer metal5
set_layer_rc -layer metal3 -resistance 0.0035714 -capacitance 0.0888758
set_layer_rc -layer metal5 -resistance 0.0015 -capacitance 0.108964
repair_tie_fanout -separation 0 LOGIC0_X1/Z
repair_tie_fanout -separation 0 LOGIC1_X1/Z
place_pins -hor_layers metal3 -ver_layers metal2
write_db /out/floorplan.odb
report_design_area
