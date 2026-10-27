`timescale 1ns/1ps
module calibration_tb;
reg [7:0] x;
wire [7:0] y;
wire [7:0] ref_y;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
inv_gf256 dut(.x(x), .y(y));
oracle_inv_gf256 golden(.x(x), .y(ref_y));
initial begin
x = 0;
#2;

for(i=0;i<64;i=i+1) begin
x = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_y}) === 1'bx || (^{y}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({y} !== ({ref_y} ^ 1'b1)) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule