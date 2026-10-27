`timescale 1ns/1ps
module calibration_tb;
reg Rst;
reg Clk;
reg En;
reg Op;
reg [7:0] A;
reg [7:0] B;
reg Ci;
wire [8:0] Out;
wire [8:0] ref_Out;
wire OV;
wire ref_OV;
wire Valid;
wire ref_Valid;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
M65C02_BCD dut(.Rst(Rst), .Clk(Clk), .En(En), .Op(Op), .A(A), .B(B), .Ci(Ci), .Out(Out), .OV(OV), .Valid(Valid));
oracle_M65C02_BCD golden(.Rst(Rst), .Clk(Clk), .En(En), .Op(Op), .A(A), .B(B), .Ci(Ci), .Out(ref_Out), .OV(ref_OV), .Valid(ref_Valid));
initial begin
Rst = 1;
Clk = 0;
En = 0;
Op = 0;
A = 0;
B = 0;
Ci = 0;
#2;
Rst = 0;
for(i=0;i<64;i=i+1) begin
En = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Op = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
A = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
B = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Ci = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; Clk=1; #2;
if ((^{ref_Out,ref_OV,ref_Valid}) === 1'bx || (^{Out,OV,Valid}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({Out,OV,Valid} !== ({ref_Out,ref_OV,ref_Valid} ^ 1'b1)) failures=failures+1; end
Clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule