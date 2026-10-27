`timescale 1ns/1ps
module calibration_tb;
reg Rst;
reg Clk;
reg CE_16x;
reg WE_RHR;
reg RE_RHR;
reg [3:0] CCntVal;
reg [3:0] RTOVal;
wire RcvTimeout;
wire ref_RcvTimeout;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
UART_RTO dut(.Rst(Rst), .Clk(Clk), .CE_16x(CE_16x), .WE_RHR(WE_RHR), .RE_RHR(RE_RHR), .CCntVal(CCntVal), .RTOVal(RTOVal), .RcvTimeout(RcvTimeout));
oracle_UART_RTO golden(.Rst(Rst), .Clk(Clk), .CE_16x(CE_16x), .WE_RHR(WE_RHR), .RE_RHR(RE_RHR), .CCntVal(CCntVal), .RTOVal(RTOVal), .RcvTimeout(ref_RcvTimeout));
initial begin
Rst = 1;
Clk = 0;
CE_16x = 0;
WE_RHR = 0;
RE_RHR = 0;
CCntVal = 0;
RTOVal = 0;
#2;
Rst = 0;
for(i=0;i<64;i=i+1) begin
CE_16x = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
WE_RHR = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
RE_RHR = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
CCntVal = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
RTOVal = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; Clk=1; #2;
if ((^{ref_RcvTimeout}) === 1'bx || (^{RcvTimeout}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({RcvTimeout} !== {ref_RcvTimeout}) failures=failures+1; end
Clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule