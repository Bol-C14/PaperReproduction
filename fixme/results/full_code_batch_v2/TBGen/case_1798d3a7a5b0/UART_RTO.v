`timescale 1ns/1ps

module UART_RTO(
    input   Rst,
    input   Clk,
    input   CE_16x,
    input   WE_RHR,
    input   RE_RHR,
    input   [3:0] CCntVal, 
    input   [3:0] RTOVal,
    output  reg RcvTimeout
);
    wire    Clr_RTOArm;
    reg     RTOArm;
    wire    Clr_BCnt;
    reg     [3:0] BCnt;
    reg     TC_BCnt;
    wire    Clr_CCnt;
    reg     [3:0] CCnt;
    reg     TC_CCnt;
    wire    Clr_RTOCnt, CE_RTOCnt;
    reg     [3:0] RTOCnt;
    reg     TC_RTOCnt;
    wire    Clr_RTO, CE_RTO;
assign Clr_RTOArm = RE_RHR | CE_RTO;
always @(posedge Clk)
begin
    if(Rst)
        RTOArm <= #1 0;
    else if(Clr_RTOArm)
        RTOArm <= #1 0;
    else if(WE_RHR)
        RTOArm <= #1 1;
end
assign Clr_BCnt = Rst | WE_RHR | Clr_RTOArm | ~RTOArm;
always @(posedge Clk)
begin
    if(Clr_BCnt)
        BCnt <= #1 0;
    else if(CE_16x)
        BCnt <= #1 BCnt + 1;
end
always @(posedge Clk)
begin
    if(Clr_BCnt)
        TC_BCnt <= #1 0;
    else if(CE_16x)
        TC_BCnt <= #1 (BCnt == 4'b1110);
end
assign Clr_CCnt = Clr_BCnt;
assign CE_CCnt = CE_16x & TC_BCnt;
always @(posedge Clk)
begin
    if(Clr_CCnt)
        CCnt <= #1 CCntVal;
    else if(CE_CCnt)
        CCnt <= #1 ((TC_CCnt) ? CCntVal : CCnt - 1);
end
always @(posedge Clk)
begin
    if(Clr_CCnt)
        TC_CCnt <= #1 0;
    else if(CE_16x)
        TC_CCnt <= #1 (CCnt == 0);
end
assign Clr_RTOCnt = Clr_BCnt;
assign CE_RTOCnt  = CE_16x & TC_BCnt & TC_CCnt;
always @(posedge Clk)
begin
    if(Clr_RTOCnt)
        RTOCnt <= #1 RTOVal;
    else if(CE_RTOCnt)
        RTOCnt <= #1 ((TC_RTOCnt) ? RTOVal : RTOCnt - 1);
end
always @(posedge Clk)
begin
    if(Clr_RTOCnt)
        TC_RTOCnt <= #1 0;
    else if(CE_16x)
        TC_RTOCnt <= #1 (RTOCnt == 0);
end
assign Clr_RTO = RE_RHR;
assign CE_RTO  = CE_16x & TC_BCnt & TC_CCnt & TC_RTOCnt;
always @(posedge Clk)
begin
    if(Rst)
        RcvTimeout <= #1 0;
    else if(Clr_RTO)
        RcvTimeout <= #1 0;
    else if(CE_RTO)
        RcvTimeout <= #1 1;
end
endmodule
