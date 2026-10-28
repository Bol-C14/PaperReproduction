create_clock -name core_clk -period 10 [get_ports clk]
set_input_delay 0.2 -clock core_clk [get_ports {resetn mem_ready mem_rdata* pcpi_wr pcpi_rd* pcpi_wait pcpi_ready irq*}]
set_output_delay 0.2 -clock core_clk [all_outputs]
