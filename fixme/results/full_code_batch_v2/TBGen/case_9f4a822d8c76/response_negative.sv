`timescale 1ns/1ps
module calibration_tb;
reg [7:0] x;
reg [7:0] y;
reg carry_in;
reg ORsel;
reg XORsel;
wire [8:0] carry_out;
wire [8:0] ref_carry_out;
wire [7:0] xor_result;
wire [7:0] ref_xor_result;
wire [7:0] or_result;
wire [7:0] ref_or_result;
wire [7:0] and_result;
wire [7:0] ref_and_result;
wire [7:0] z;
wire [7:0] ref_z;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
alu_adder dut(.x(x), .y(y), .carry_in(carry_in), .ORsel(ORsel), .XORsel(XORsel), .carry_out(carry_out), .xor_result(xor_result), .or_result(or_result), .and_result(and_result), .z(z));
oracle_alu_adder golden(.x(x), .y(y), .carry_in(carry_in), .ORsel(ORsel), .XORsel(XORsel), .carry_out(ref_carry_out), .xor_result(ref_xor_result), .or_result(ref_or_result), .and_result(ref_and_result), .z(ref_z));
initial begin
x = 0;
y = 0;
carry_in = 0;
ORsel = 0;
XORsel = 0;
#2;

for(i=0;i<64;i=i+1) begin
x = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
y = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
carry_in = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ORsel = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
XORsel = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_carry_out,ref_xor_result,ref_or_result,ref_and_result,ref_z}) === 1'bx || (^{carry_out,xor_result,or_result,and_result,z}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({carry_out,xor_result,or_result,and_result,z} !== ({ref_carry_out,ref_xor_result,ref_or_result,ref_and_result,ref_z} ^ 1'b1)) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule