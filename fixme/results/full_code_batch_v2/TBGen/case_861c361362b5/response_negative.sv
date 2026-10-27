`timescale 1ns/1ps
module calibration_tb;
reg [7:0] B;
wire [7:0] R;
wire [7:0] ref_R;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
RsDecodeInv dut(.B(B), .R(R));
oracle_RsDecodeInv golden(.B(B), .R(ref_R));
initial begin
B = 0;
#2;

for(i=0;i<64;i=i+1) begin
B = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_R}) === 1'bx || (^{R}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({R} !== ({ref_R} ^ 1'b1)) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule