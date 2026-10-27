`timescale 1ns/1ps
module calibration_tb;
reg INA;
reg INB;
reg INC;
wire PPBIT;
wire ref_PPBIT;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
R_GATE dut(.INA(INA), .INB(INB), .INC(INC), .PPBIT(PPBIT));
oracle_R_GATE golden(.INA(INA), .INB(INB), .INC(INC), .PPBIT(ref_PPBIT));
initial begin
INA = 0;
INB = 0;
INC = 0;
#2;

for(i=0;i<64;i=i+1) begin
INA = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
INB = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
INC = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_PPBIT}) === 1'bx || (^{PPBIT}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({PPBIT} !== ({ref_PPBIT} ^ 1'b1)) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule