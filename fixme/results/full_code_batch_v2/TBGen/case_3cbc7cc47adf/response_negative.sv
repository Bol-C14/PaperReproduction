`timescale 1ns/1ps
module calibration_tb;
reg radical;
reg clk;
reg ena;
reg aclr;
wire q;
wire ref_q;
wire remainder;
wire ref_remainder;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
altsqrt dut(.radical(radical), .clk(clk), .ena(ena), .aclr(aclr), .q(q), .remainder(remainder));
oracle_altsqrt golden(.radical(radical), .clk(clk), .ena(ena), .aclr(aclr), .q(ref_q), .remainder(ref_remainder));
initial begin
radical = 0;
clk = 0;
ena = 0;
aclr = 0;
#2;

for(i=0;i<64;i=i+1) begin
radical = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ena = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
aclr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_q,ref_remainder}) === 1'bx || (^{q,remainder}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({q,remainder} !== ({ref_q,ref_remainder} ^ 1'b1)) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule