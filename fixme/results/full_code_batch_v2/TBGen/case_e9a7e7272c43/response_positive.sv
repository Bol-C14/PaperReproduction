`timescale 1ns/1ps
module calibration_tb;
wire [15:0] cop_counter;
wire [15:0] ref_cop_counter;
wire [15:0] cop_capture;
wire [15:0] ref_cop_capture;
wire cop_rst_o;
wire ref_cop_rst_o;
wire cop_irq_o;
wire ref_cop_irq_o;
wire cop_event;
wire ref_cop_event;
reg async_rst_b;
reg sync_reset;
reg por_reset_i;
reg startup_osc_i;
reg bus_clk;
reg reload_count;
reg clear_event;
reg debug_mode_i;
reg debug_ena;
reg wait_ena;
reg wait_mode_i;
reg stop_ena;
reg stop_mode_i;
reg cop_ena;
reg [1:0] cop_irq_en;
reg [15:0] timeout_value;
reg scantestmode;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
cop_count dut(.cop_counter(cop_counter), .cop_capture(cop_capture), .cop_rst_o(cop_rst_o), .cop_irq_o(cop_irq_o), .cop_event(cop_event), .async_rst_b(async_rst_b), .sync_reset(sync_reset), .por_reset_i(por_reset_i), .startup_osc_i(startup_osc_i), .bus_clk(bus_clk), .reload_count(reload_count), .clear_event(clear_event), .debug_mode_i(debug_mode_i), .debug_ena(debug_ena), .wait_ena(wait_ena), .wait_mode_i(wait_mode_i), .stop_ena(stop_ena), .stop_mode_i(stop_mode_i), .cop_ena(cop_ena), .cop_irq_en(cop_irq_en), .timeout_value(timeout_value), .scantestmode(scantestmode));
oracle_cop_count golden(.cop_counter(ref_cop_counter), .cop_capture(ref_cop_capture), .cop_rst_o(ref_cop_rst_o), .cop_irq_o(ref_cop_irq_o), .cop_event(ref_cop_event), .async_rst_b(async_rst_b), .sync_reset(sync_reset), .por_reset_i(por_reset_i), .startup_osc_i(startup_osc_i), .bus_clk(bus_clk), .reload_count(reload_count), .clear_event(clear_event), .debug_mode_i(debug_mode_i), .debug_ena(debug_ena), .wait_ena(wait_ena), .wait_mode_i(wait_mode_i), .stop_ena(stop_ena), .stop_mode_i(stop_mode_i), .cop_ena(cop_ena), .cop_irq_en(cop_irq_en), .timeout_value(timeout_value), .scantestmode(scantestmode));
initial begin
async_rst_b = 0;
sync_reset = 1;
por_reset_i = 1;
startup_osc_i = 0;
bus_clk = 0;
reload_count = 0;
clear_event = 0;
debug_mode_i = 0;
debug_ena = 0;
wait_ena = 0;
wait_mode_i = 0;
stop_ena = 0;
stop_mode_i = 0;
cop_ena = 0;
cop_irq_en = 0;
timeout_value = 0;
scantestmode = 0;
#2;
async_rst_b = 1;
sync_reset = 0;
por_reset_i = 0;
for(i=0;i<64;i=i+1) begin
startup_osc_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
reload_count = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
clear_event = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
debug_mode_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
debug_ena = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wait_ena = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wait_mode_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
stop_ena = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
stop_mode_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
cop_ena = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
cop_irq_en = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
timeout_value = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
scantestmode = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; bus_clk=1; #2;
if ((^{ref_cop_counter,ref_cop_capture,ref_cop_rst_o,ref_cop_irq_o,ref_cop_event}) === 1'bx || (^{cop_counter,cop_capture,cop_rst_o,cop_irq_o,cop_event}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({cop_counter,cop_capture,cop_rst_o,cop_irq_o,cop_event} !== {ref_cop_counter,ref_cop_capture,ref_cop_rst_o,ref_cop_irq_o,ref_cop_event}) failures=failures+1; end
bus_clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule