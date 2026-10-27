`timescale 1ns/1ps
module calibration_tb;
reg A1;
reg A2;
wire ZN;
wire ref_ZN;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
AND2_X1 dut(.A1(A1), .A2(A2), .ZN(ZN));
oracle_AND2_X1 golden(.A1(A1), .A2(A2), .ZN(ref_ZN));
initial begin
A1 = 0;
A2 = 0;
#2;

for(i=0;i<64;i=i+1) begin
A1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
A2 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_ZN}) === 1'bx || (^{ZN}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({ZN} !== ({ref_ZN} ^ 1'b1)) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule