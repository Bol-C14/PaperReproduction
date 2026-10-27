`timescale 1ns/1ps
module calibration_tb;
reg Rst;
reg Clk;
reg CE;
reg [11:0] ALU_Op;
reg WE_PSW;
reg [7:0] DI;
reg [7:0] KI;
wire [7:0] DO;
wire [7:0] ref_DO;
wire Z_Tst;
wire ref_Z_Tst;
wire g;
wire ref_g;
wire [7:0] W;
wire [7:0] ref_W;
wire Z;
wire ref_Z;
wire DC;
wire ref_DC;
wire C;
wire ref_C;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
P16C5x_ALU dut(.Rst(Rst), .Clk(Clk), .CE(CE), .ALU_Op(ALU_Op), .WE_PSW(WE_PSW), .DI(DI), .KI(KI), .DO(DO), .Z_Tst(Z_Tst), .g(g), .W(W), .Z(Z), .DC(DC), .C(C));
oracle_P16C5x_ALU golden(.Rst(Rst), .Clk(Clk), .CE(CE), .ALU_Op(ALU_Op), .WE_PSW(WE_PSW), .DI(DI), .KI(KI), .DO(ref_DO), .Z_Tst(ref_Z_Tst), .g(ref_g), .W(ref_W), .Z(ref_Z), .DC(ref_DC), .C(ref_C));
initial begin
Rst = 1;
Clk = 0;
CE = 0;
ALU_Op = 0;
WE_PSW = 0;
DI = 0;
KI = 0;
#2;
Rst = 0;
for(i=0;i<64;i=i+1) begin
CE = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ALU_Op = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
WE_PSW = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
DI = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
KI = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; Clk=1; #2;
if ((^{ref_DO,ref_Z_Tst,ref_g,ref_W,ref_Z,ref_DC,ref_C}) === 1'bx || (^{DO,Z_Tst,g,W,Z,DC,C}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({DO,Z_Tst,g,W,Z,DC,C} !== {ref_DO,ref_Z_Tst,ref_g,ref_W,ref_Z,ref_DC,ref_C}) failures=failures+1; end
Clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule