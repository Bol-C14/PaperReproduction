`timescale 1ns/1ps
module oracle_UART_RXSM(
    input   Rst,
    input   Clk,
    input   CE_16x,         
    input   Len,            
    input   NumStop,        
    input   ParEn,          
    input   [1:0] Par,      
    input   RxD,            
    output  reg [8:0] RD,   
    output  reg WE_RHR,     
    output  RxWait,         
    output  RxIdle,         
    output  RxStart,        
    output  RxShift,        
    output  RxParity,       
    output  RxStop,         
    output  RxError         
);
localparam pWaitMark  =  0;
localparam pChkMark   =  1;
localparam pIdle      =  3;
localparam pChkStart  =  2;
localparam pShift0    = 10;
localparam pShift1    = 11;
localparam pShift2    =  9;
localparam pShift3    =  8;
localparam pShift4    = 12;
localparam pShift5    = 13;
localparam pShift6    = 15;
localparam pShift7    = 14;
localparam pChkStop1  =  6;
localparam pChkStop2  =  7;
localparam pChkParity =  5;
localparam pRcvError  =  4;
    (* FSM_ENCODING="SEQUENTIAL", 
       SAFE_IMPLEMENTATION="YES", 
       SAFE_RECOVERY_STATE="4'b0" *) reg [3:0] RxSM = pWaitMark;
    reg     [3:0] BCnt;
    reg     [7:0] RSR;
    reg     Err;
assign RxSM_Wait = (  (RxSM == pWaitMark)
                    | (RxSM == pChkMark)
                    | (RxSM == pIdle)
                    | (RxSM == pRcvError) );
assign RxWait   = RxSM_Wait;
assign RxIdle   = (RxSM == pIdle);
assign RxStart  = (RxSM == pChkStart);
assign RxShift  = (  (RxSM == pShift0) 
                   | (RxSM == pShift1) 
                   | (RxSM == pShift2)
                   | (RxSM == pShift3)
                   | (RxSM == pShift4)
                   | (RxSM == pShift5)
                   | (RxSM == pShift6)
                   | (RxSM == pShift7) );
assign RxParity = (RxSM == pChkParity);
assign RxStop   = (RxSM == pChkStop1) | (RxSM == pChkStop2);
assign RxError  = (RxSM == pRcvError);
assign Rst_BCnt = Rst | RxSM_Wait;
always @(posedge Clk)
begin
    if(Rst_BCnt)
         BCnt <= #1 4'b1000;
    else if(CE_16x)
         BCnt <= #1 BCnt + 1;
end
assign TC_BCnt = CE_16x & (BCnt == 4'b1111);
assign CE_RxSM = (RxSM_Wait ? CE_16x : TC_BCnt);
always @(posedge Clk)
begin
    if(Rst)
         RSR <= #1 8'b0;
    else if(CE_RxSM)
        case(RxSM)
            pChkStart :  RSR    <= #1 8'b0; 
            pShift0   :  RSR[0] <= #1 RxD;
            pShift1   :  RSR[1] <= #1 RxD;
            pShift2   :  RSR[2] <= #1 RxD;
            pShift3   :  RSR[3] <= #1 RxD;
            pShift4   :  RSR[4] <= #1 RxD;
            pShift5   :  RSR[5] <= #1 RxD;
            pShift6   :  RSR[6] <= #1 RxD;
            pShift7   :  RSR[7] <= #1 RxD;
            default   :  RSR    <= #1 RSR;
        endcase
end
assign OddPar = ^{RxD, RSR};
assign EvnPar = ~OddPar;
always @(*)
begin
    case(Par)
        2'b00 : Err <= ~OddPar;
        2'b01 : Err <= ~EvnPar;
        2'b10 : Err <=  RxD;
        2'b11 : Err <= ~RxD;
    endcase
end
assign ParErr = Err & (RxSM == pChkParity);
assign CE_RD = CE_RxSM & (((RxSM == pChkStop1) & RxD) | (RxSM == pRcvError));
always @(posedge Clk)
begin
    if(Rst)
         RD <= #1 9'b0;
    else if(CE_RD)
         RD <= #1 {(RxSM == pRcvError), RSR};
end
always @(posedge Clk)
begin
    if(Rst)
         WE_RHR <= #1 1'b0;
    else
         WE_RHR <= #1 CE_RD;
end
always @(posedge Clk)
begin
    if(Rst)
         RxSM <= #1 pWaitMark;
    else if(CE_RxSM)
        case(RxSM)
            pWaitMark  :  RxSM <= #1 ( RxD ? pChkMark 
                                           : pWaitMark);
            pChkMark   :  RxSM <= #1 ( RxD ? pIdle 
                                           : pWaitMark);
            pIdle      :  RxSM <= #1 (~RxD ? pChkStart 
                                           : pIdle);
            pChkStart  :  RxSM <= #1 ( RxD ? pIdle 
                                           : pShift0);
            pShift0    :  RxSM <= #1 pShift1;
            pShift1    :  RxSM <= #1 pShift2;
            pShift2    :  RxSM <= #1 pShift3;
            pShift3    :  RxSM <= #1 pShift4;
            pShift4    :  RxSM <= #1 pShift5;
            pShift5    :  RxSM <= #1 pShift6;
            pShift6    :  RxSM <= #1 (Len    ? pChkParity 
                                             : pShift7);
            pShift7    :  RxSM <= #1 (ParEn  ? pChkParity
                                             : (NumStop ? pChkStop2 
                                                        : pChkStop1));
            pChkParity :  RxSM <= #1 (ParErr ? pRcvError 
                                             : (NumStop ? pChkStop2 
                                                        : pChkStop1));
            pChkStop2  :  RxSM <= #1 (RxD ? pChkStop1 
                                          : pRcvError);
            pChkStop1  :  RxSM <= #1 (RxD ? pIdle 
                                          : pRcvError);
            pRcvError  :  RxSM <= #1 pWaitMark;
            default    :  RxSM <= #1 pWaitMark;
        endcase
end
endmodule