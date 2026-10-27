`timescale 1ns/1ps
module calibration_tb;
reg in;
wire out;
wire ref_out;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
delay dut(.in(in), .out(out));
oracle_delay golden(.in(in), .out(ref_out));
initial begin
in = 0;
#2;

for(i=0;i<64;i=i+1) begin
in = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_out}) === 1'bx || (^{out}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({out} !== {ref_out}) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule