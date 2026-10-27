`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg [7:0] addr;
wire [17:0] c0;
wire [17:0] ref_c0;
wire [17:0] c1;
wire [17:0] ref_c1;
wire [16:0] c2;
wire [16:0] ref_c2;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
gng_coef dut(.clk(clk), .addr(addr), .c0(c0), .c1(c1), .c2(c2));
oracle_gng_coef golden(.clk(clk), .addr(addr), .c0(ref_c0), .c1(ref_c1), .c2(ref_c2));
initial begin
clk = 0;
addr = 0;
#2;

for(i=0;i<64;i=i+1) begin
addr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_c0,ref_c1,ref_c2}) === 1'bx || (^{c0,c1,c2}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({c0,c1,c2} !== {ref_c0,ref_c1,ref_c2}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule