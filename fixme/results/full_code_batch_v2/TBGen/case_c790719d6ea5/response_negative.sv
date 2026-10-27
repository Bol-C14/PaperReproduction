`timescale 1ns/1ps
module calibration_tb;
wire dout;
wire ref_dout;
reg in0;
reg in1;
reg sel;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
dp_mux2es dut(.dout(dout), .in0(in0), .in1(in1), .sel(sel));
oracle_dp_mux2es golden(.dout(ref_dout), .in0(in0), .in1(in1), .sel(sel));
initial begin
in0 = 0;
in1 = 0;
sel = 0;
#2;

for(i=0;i<64;i=i+1) begin
in0 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
in1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
sel = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_dout}) === 1'bx || (^{dout}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({dout} !== ({ref_dout} ^ 1'b1)) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule