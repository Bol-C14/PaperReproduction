`timescale 1ns/1ps
module calibration_tb;
reg din;
reg clk;
reg rst;
wire q;
wire ref_q;
reg se;
reg si;
wire so;
wire ref_so;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
dffr_async dut(.din(din), .clk(clk), .rst(rst), .q(q), .se(se), .si(si), .so(so));
oracle_dffr_async golden(.din(din), .clk(clk), .rst(rst), .q(ref_q), .se(se), .si(si), .so(ref_so));
initial begin
din = 0;
clk = 0;
rst = 1;
se = 0;
si = 0;
#2;
rst = 0;
for(i=0;i<64;i=i+1) begin
din = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
se = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
si = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_q,ref_so}) === 1'bx || (^{q,so}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({q,so} !== ({ref_q,ref_so} ^ 1'b1)) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule