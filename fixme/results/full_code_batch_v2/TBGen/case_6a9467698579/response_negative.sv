`timescale 1ns/1ps
module calibration_tb;
reg [4:0] in1;
reg [4:0] in2;
wire [4:0] out;
wire [4:0] ref_out;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
gfadder dut(.in1(in1), .in2(in2), .out(out));
oracle_gfadder golden(.in1(in1), .in2(in2), .out(ref_out));
initial begin
in1 = 0;
in2 = 0;
#2;

for(i=0;i<64;i=i+1) begin
in1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
in2 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_out}) === 1'bx || (^{out}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({out} !== ({ref_out} ^ 1'b1)) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule