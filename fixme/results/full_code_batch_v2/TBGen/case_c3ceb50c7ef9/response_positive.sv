`timescale 1ns/1ps
module calibration_tb;
reg [10:0] address;
reg clock;
wire [11:0] q;
wire [11:0] ref_q;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
sim_rom dut(.address(address), .clock(clock), .q(q));
oracle_sim_rom golden(.address(address), .clock(clock), .q(ref_q));
initial begin
address = 0;
clock = 0;
#2;

for(i=0;i<64;i=i+1) begin
address = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clock=1; #2;
if ((^{ref_q}) === 1'bx || (^{q}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({q} !== {ref_q}) failures=failures+1; end
clock=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule