`timescale 1ns/1ps
module calibration_tb;
wire [11:0] fill_level;
wire [11:0] ref_fill_level;
reg clk;
reg reset;
wire in_ready;
wire ref_in_ready;
reg in_valid;
reg [10:0] in_data;
reg out_ready;
wire out_valid;
wire ref_out_valid;
wire [10:0] out_data;
wire [10:0] ref_out_data;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
loopback_adapter_fifo dut(.fill_level(fill_level), .clk(clk), .reset(reset), .in_ready(in_ready), .in_valid(in_valid), .in_data(in_data), .out_ready(out_ready), .out_valid(out_valid), .out_data(out_data));
oracle_loopback_adapter_fifo golden(.fill_level(ref_fill_level), .clk(clk), .reset(reset), .in_ready(ref_in_ready), .in_valid(in_valid), .in_data(in_data), .out_ready(out_ready), .out_valid(ref_out_valid), .out_data(ref_out_data));
initial begin
clk = 0;
reset = 1;
in_valid = 0;
in_data = 0;
out_ready = 0;
#2;
reset = 0;
for(i=0;i<64;i=i+1) begin
in_valid = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
in_data = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
out_ready = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_fill_level,ref_in_ready,ref_out_valid,ref_out_data}) === 1'bx || (^{fill_level,in_ready,out_valid,out_data}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({fill_level,in_ready,out_valid,out_data} !== {ref_fill_level,ref_in_ready,ref_out_valid,ref_out_data}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule