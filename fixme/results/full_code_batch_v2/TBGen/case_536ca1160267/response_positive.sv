`timescale 1ns/1ps
module calibration_tb;
reg Rst;
reg Clk;
reg CE_16x;
reg Len;
reg NumStop;
reg ParEn;
reg [1:0] Par;
reg RxD;
wire [8:0] RD;
wire [8:0] ref_RD;
wire WE_RHR;
wire ref_WE_RHR;
wire RxWait;
wire ref_RxWait;
wire RxIdle;
wire ref_RxIdle;
wire RxStart;
wire ref_RxStart;
wire RxShift;
wire ref_RxShift;
wire RxParity;
wire ref_RxParity;
wire RxStop;
wire ref_RxStop;
wire RxError;
wire ref_RxError;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
UART_RXSM dut(.Rst(Rst), .Clk(Clk), .CE_16x(CE_16x), .Len(Len), .NumStop(NumStop), .ParEn(ParEn), .Par(Par), .RxD(RxD), .RD(RD), .WE_RHR(WE_RHR), .RxWait(RxWait), .RxIdle(RxIdle), .RxStart(RxStart), .RxShift(RxShift), .RxParity(RxParity), .RxStop(RxStop), .RxError(RxError));
oracle_UART_RXSM golden(.Rst(Rst), .Clk(Clk), .CE_16x(CE_16x), .Len(Len), .NumStop(NumStop), .ParEn(ParEn), .Par(Par), .RxD(RxD), .RD(ref_RD), .WE_RHR(ref_WE_RHR), .RxWait(ref_RxWait), .RxIdle(ref_RxIdle), .RxStart(ref_RxStart), .RxShift(ref_RxShift), .RxParity(ref_RxParity), .RxStop(ref_RxStop), .RxError(ref_RxError));
initial begin
Rst = 1;
Clk = 0;
CE_16x = 0;
Len = 0;
NumStop = 0;
ParEn = 0;
Par = 0;
RxD = 0;
#2;
Rst = 0;
for(i=0;i<64;i=i+1) begin
CE_16x = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Len = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
NumStop = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ParEn = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Par = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
RxD = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; Clk=1; #2;
if ((^{ref_RD,ref_WE_RHR,ref_RxWait,ref_RxIdle,ref_RxStart,ref_RxShift,ref_RxParity,ref_RxStop,ref_RxError}) === 1'bx || (^{RD,WE_RHR,RxWait,RxIdle,RxStart,RxShift,RxParity,RxStop,RxError}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({RD,WE_RHR,RxWait,RxIdle,RxStart,RxShift,RxParity,RxStop,RxError} !== {ref_RD,ref_WE_RHR,ref_RxWait,ref_RxIdle,ref_RxStart,ref_RxShift,ref_RxParity,ref_RxStop,ref_RxError}) failures=failures+1; end
Clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule