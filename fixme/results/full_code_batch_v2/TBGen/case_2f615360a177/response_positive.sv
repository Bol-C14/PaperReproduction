`timescale 1ns/1ps
module calibration_tb;
reg clock;
reg reset;
reg enable;
reg [31:0] D;
wire [31:0] Q;
wire [31:0] ref_Q;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
Register dut(.clock(clock), .reset(reset), .enable(enable), .D(D), .Q(Q));
oracle_Register golden(.clock(clock), .reset(reset), .enable(enable), .D(D), .Q(ref_Q));
initial begin
clock = 0;
reset = 1;
enable = 0;
D = 0;
#2;
reset = 0;
for(i=0;i<64;i=i+1) begin
enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
D = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clock=1; #2;
if ((^{ref_Q}) === 1'bx || (^{Q}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({Q} !== {ref_Q}) failures=failures+1; end
clock=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule