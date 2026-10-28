create_clock -period 100 -name clk [get_ports clk]
set_input_delay 0 -max -rise [get_ports a] -clock clk
set_input_transition 10 -max -rise [get_ports a] -clock clk
set_output_delay 20 -max -rise [get_ports y0] -clock clk
set_output_delay 20 -max -rise [get_ports y1] -clock clk
set_output_delay 20 -max -rise [get_ports y2] -clock clk
set_output_delay 20 -max -rise [get_ports y3] -clock clk
set_output_delay 20 -max -rise [get_ports y4] -clock clk
set_output_delay 20 -max -rise [get_ports y5] -clock clk
set_output_delay 20 -max -rise [get_ports y6] -clock clk
set_output_delay 20 -max -rise [get_ports y7] -clock clk
set_output_delay 20 -max -rise [get_ports y8] -clock clk
set_output_delay 20 -max -rise [get_ports y9] -clock clk
set_input_delay 0 -max -fall [get_ports a] -clock clk
set_input_transition 10 -max -fall [get_ports a] -clock clk
set_output_delay 20 -max -fall [get_ports y0] -clock clk
set_output_delay 20 -max -fall [get_ports y1] -clock clk
set_output_delay 20 -max -fall [get_ports y2] -clock clk
set_output_delay 20 -max -fall [get_ports y3] -clock clk
set_output_delay 20 -max -fall [get_ports y4] -clock clk
set_output_delay 20 -max -fall [get_ports y5] -clock clk
set_output_delay 20 -max -fall [get_ports y6] -clock clk
set_output_delay 20 -max -fall [get_ports y7] -clock clk
set_output_delay 20 -max -fall [get_ports y8] -clock clk
set_output_delay 20 -max -fall [get_ports y9] -clock clk
set_load -pin_load 1.44 [get_ports y0]
set_load -pin_load 1.44 [get_ports y1]
set_load -pin_load 1.44 [get_ports y2]
set_load -pin_load 1.44 [get_ports y3]
set_load -pin_load 1.44 [get_ports y4]
set_load -pin_load 1.44 [get_ports y5]
set_load -pin_load 1.44 [get_ports y6]
set_load -pin_load 1.44 [get_ports y7]
set_load -pin_load 1.44 [get_ports y8]
set_load -pin_load 1.44 [get_ports y9]
