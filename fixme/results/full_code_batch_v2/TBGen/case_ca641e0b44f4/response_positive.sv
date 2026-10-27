`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg rst;
reg enable;
reg [63:0] opa;
reg [63:0] opb;
wire sign;
wire ref_sign;
wire [55:0] mantissa_7;
wire [55:0] ref_mantissa_7;
wire [11:0] exponent_out;
wire [11:0] ref_exponent_out;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
fpu_div dut(.clk(clk), .rst(rst), .enable(enable), .opa(opa), .opb(opb), .sign(sign), .mantissa_7(mantissa_7), .exponent_out(exponent_out));
oracle_fpu_div golden(.clk(clk), .rst(rst), .enable(enable), .opa(opa), .opb(opb), .sign(ref_sign), .mantissa_7(ref_mantissa_7), .exponent_out(ref_exponent_out));
initial begin
clk = 0;
rst = 1;
enable = 0;
opa = 0;
opb = 0;
#2;
rst = 0;
for(i=0;i<64;i=i+1) begin
enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opa = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opb = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_sign,ref_mantissa_7,ref_exponent_out}) === 1'bx || (^{sign,mantissa_7,exponent_out}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({sign,mantissa_7,exponent_out} !== {ref_sign,ref_mantissa_7,ref_exponent_out}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule