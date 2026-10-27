`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg [63:0] B;
reg [63:0] R;
reg [2:0] X;
reg [2:0] Y;
reg player;
wire [63:0] MB;
wire [63:0] ref_MB;
wire [63:0] MR;
wire [63:0] ref_MR;
reg RST;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
board_move dut(.clk(clk), .B(B), .R(R), .X(X), .Y(Y), .player(player), .MB(MB), .MR(MR), .RST(RST));
oracle_board_move golden(.clk(clk), .B(B), .R(R), .X(X), .Y(Y), .player(player), .MB(ref_MB), .MR(ref_MR), .RST(RST));
initial begin
clk = 0;
B = 0;
R = 0;
X = 0;
Y = 0;
player = 0;
RST = 1;
#2;
RST = 0;
for(i=0;i<64;i=i+1) begin
B = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
R = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
X = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Y = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
player = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_MB,ref_MR}) === 1'bx || (^{MB,MR}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({MB,MR} !== {ref_MB,ref_MR}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule