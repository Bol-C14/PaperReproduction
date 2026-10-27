`timescale 1ns/1ps
module calibration_tb;
reg [7:0] x;
reg [7:0] y;
wire [7:0] z;
wire [7:0] ref_z;
wire c;
wire ref_c;
reg direction;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
alu_barrel_shifter dut(.x(x), .y(y), .z(z), .c(c), .direction(direction));
oracle_alu_barrel_shifter golden(.x(x), .y(y), .z(ref_z), .c(ref_c), .direction(direction));
initial begin
x = 0;
y = 0;
direction = 0;
#2;

for(i=0;i<64;i=i+1) begin
x = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
y = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
direction = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_z,ref_c}) === 1'bx || (^{z,c}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({z,c} !== ({ref_z,ref_c} ^ 1'b1)) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule