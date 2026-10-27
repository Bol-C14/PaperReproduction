`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg rst;
reg enable_i;
reg d_in;
wire valid_o;
wire ref_valid_o;
wire [1:0] d_out;
wire [1:0] ref_d_out;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
encoder dut(.clk(clk), .rst(rst), .enable_i(enable_i), .d_in(d_in), .valid_o(valid_o), .d_out(d_out));
oracle_encoder golden(.clk(clk), .rst(rst), .enable_i(enable_i), .d_in(d_in), .valid_o(ref_valid_o), .d_out(ref_d_out));
initial begin
clk = 0;
rst = 1;
enable_i = 0;
d_in = 0;
#2;
rst = 0;
for(i=0;i<64;i=i+1) begin
enable_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
d_in = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_valid_o,ref_d_out}) === 1'bx || (^{valid_o,d_out}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({valid_o,d_out} !== ({ref_valid_o,ref_d_out} ^ 1'b1)) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule