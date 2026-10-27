`timescale 1ns/1ps
module calibration_tb;
reg Rst;
reg Clk;
reg LSB;
reg [1:0] Mode;
reg [2:0] Rate;
reg DAV;
wire FRE;
wire ref_FRE;
reg [8:0] TD;
wire FWE;
wire ref_FWE;
wire [7:0] RD;
wire [7:0] ref_RD;
wire SS;
wire ref_SS;
wire SCK;
wire ref_SCK;
wire MOSI;
wire ref_MOSI;
reg MISO;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
SPIxIF dut(.Rst(Rst), .Clk(Clk), .LSB(LSB), .Mode(Mode), .Rate(Rate), .DAV(DAV), .FRE(FRE), .TD(TD), .FWE(FWE), .RD(RD), .SS(SS), .SCK(SCK), .MOSI(MOSI), .MISO(MISO));
oracle_SPIxIF golden(.Rst(Rst), .Clk(Clk), .LSB(LSB), .Mode(Mode), .Rate(Rate), .DAV(DAV), .FRE(ref_FRE), .TD(TD), .FWE(ref_FWE), .RD(ref_RD), .SS(ref_SS), .SCK(ref_SCK), .MOSI(ref_MOSI), .MISO(MISO));
initial begin
Rst = 1;
Clk = 0;
LSB = 0;
Mode = 0;
Rate = 0;
DAV = 0;
TD = 0;
MISO = 0;
#2;
Rst = 0;
for(i=0;i<64;i=i+1) begin
LSB = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Mode = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Rate = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
DAV = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
TD = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
MISO = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; Clk=1; #2;
if ((^{ref_FRE,ref_FWE,ref_RD,ref_SS,ref_SCK,ref_MOSI}) === 1'bx || (^{FRE,FWE,RD,SS,SCK,MOSI}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({FRE,FWE,RD,SS,SCK,MOSI} !== {ref_FRE,ref_FWE,ref_RD,ref_SS,ref_SCK,ref_MOSI}) failures=failures+1; end
Clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule