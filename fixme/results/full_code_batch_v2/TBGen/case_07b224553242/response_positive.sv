`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg rst;
reg enable;
reg [1:0] rmode;
reg [63:0] opa;
reg [63:0] opb;
wire ready;
wire ref_ready;
wire [63:0] outfp;
wire [63:0] ref_outfp;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
fpu_mul dut(.clk(clk), .rst(rst), .enable(enable), .rmode(rmode), .opa(opa), .opb(opb), .ready(ready), .outfp(outfp));
oracle_fpu_mul golden(.clk(clk), .rst(rst), .enable(enable), .rmode(rmode), .opa(opa), .opb(opb), .ready(ref_ready), .outfp(ref_outfp));
initial begin
clk = 0;
rst = 1;
enable = 0;
rmode = 0;
opa = 0;
opb = 0;
#2;
rst = 0;
for(i=0;i<64;i=i+1) begin
enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rmode = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opa = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opb = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_ready,ref_outfp}) === 1'bx || (^{ready,outfp}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({ready,outfp} !== {ref_ready,ref_outfp}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule