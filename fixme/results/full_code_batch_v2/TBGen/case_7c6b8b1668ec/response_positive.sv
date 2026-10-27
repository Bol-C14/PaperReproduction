`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg we;
reg [3:0] a;
reg [3:0] dpra;
reg [7:0] di;
wire [7:0] dpo;
wire [7:0] ref_dpo;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
raminfr dut(.clk(clk), .we(we), .a(a), .dpra(dpra), .di(di), .dpo(dpo));
oracle_raminfr golden(.clk(clk), .we(we), .a(a), .dpra(dpra), .di(di), .dpo(ref_dpo));
initial begin
clk = 0;
we = 0;
a = 0;
dpra = 0;
di = 0;
#2;

for(i=0;i<64;i=i+1) begin
we = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
a = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
dpra = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
di = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_dpo}) === 1'bx || (^{dpo}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({dpo} !== {ref_dpo}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule