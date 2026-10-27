`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg rst;
reg enable;
reg [63:0] opa;
reg [63:0] opb;
reg [2:0] fpu_op;
wire sign;
wire ref_sign;
wire [55:0] diff_2;
wire [55:0] ref_diff_2;
wire [10:0] exponent_2;
wire [10:0] ref_exponent_2;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
fpu_sub dut(.clk(clk), .rst(rst), .enable(enable), .opa(opa), .opb(opb), .fpu_op(fpu_op), .sign(sign), .diff_2(diff_2), .exponent_2(exponent_2));
oracle_fpu_sub golden(.clk(clk), .rst(rst), .enable(enable), .opa(opa), .opb(opb), .fpu_op(fpu_op), .sign(ref_sign), .diff_2(ref_diff_2), .exponent_2(ref_exponent_2));
initial begin
clk = 0;
rst = 1;
enable = 0;
opa = 0;
opb = 0;
fpu_op = 0;
#2;
rst = 0;
for(i=0;i<64;i=i+1) begin
enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opa = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opb = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
fpu_op = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_sign,ref_diff_2,ref_exponent_2}) === 1'bx || (^{sign,diff_2,exponent_2}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({sign,diff_2,exponent_2} !== {ref_sign,ref_diff_2,ref_exponent_2}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule