`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg rst;
reg enable;
reg fpu_op;
reg [1:0] rmode;
reg [63:0] opa;
reg [63:0] opb;
wire [63:0] out;
wire [63:0] ref_out;
wire ready;
wire ref_ready;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
fpu_addsub dut(.clk(clk), .rst(rst), .enable(enable), .fpu_op(fpu_op), .rmode(rmode), .opa(opa), .opb(opb), .out(out), .ready(ready));
oracle_fpu_addsub golden(.clk(clk), .rst(rst), .enable(enable), .fpu_op(fpu_op), .rmode(rmode), .opa(opa), .opb(opb), .out(ref_out), .ready(ref_ready));
initial begin
clk = 0;
rst = 1;
enable = 0;
fpu_op = 0;
rmode = 0;
opa = 0;
opb = 0;
#2;
rst = 0;
for(i=0;i<64;i=i+1) begin
enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
fpu_op = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rmode = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opa = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opb = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_out,ref_ready}) === 1'bx || (^{out,ready}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({out,ready} !== {ref_out,ref_ready}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule