`timescale 1ns/1ps
 
module ref_eth_receivecontrol (MTxClk, MRxClk, TxReset, RxReset, RxData, RxValid, RxStartFrm, 
                           RxEndFrm, RxFlow, ReceiveEnd, MAC, DlyCrcEn, TxDoneIn, 
                           TxAbortIn, TxStartFrmOut, ReceivedLengthOK, ReceivedPacketGood, 
                           TxUsedDataOutDetected, ref_Pause, ref_ReceivedPauseFrm, ref_AddressOK, 
                           RxStatusWriteLatched_sync2, r_PassAll, ref_SetPauseTimer
                          );
input       MTxClk;
input       MRxClk;
input       TxReset; 
input       RxReset; 
input [7:0] RxData;
input       RxValid;
input       RxStartFrm;
input       RxEndFrm;
input       RxFlow;
input       ReceiveEnd;
input [47:0]MAC;
input       DlyCrcEn;
input       TxDoneIn;
input       TxAbortIn;
input       TxStartFrmOut;
input       ReceivedLengthOK;
input       ReceivedPacketGood;
input       TxUsedDataOutDetected;
input       RxStatusWriteLatched_sync2;
input       r_PassAll;
output      ref_Pause;
output      ref_ReceivedPauseFrm;
output      ref_AddressOK;
output      ref_SetPauseTimer;
reg         ref_Pause;
reg         ref_AddressOK;                
reg         TypeLengthOK;             
reg         DetectionWindow;          
reg         OpCodeOK;                 
reg  [2:0]  DlyCrcCnt;
reg  [4:0]  ByteCnt;
reg [15:0]  AssembledTimerValue;
reg [15:0]  LatchedTimerValue;
reg         ref_ReceivedPauseFrm;
reg         ReceivedPauseFrmWAddr;
reg         PauseTimerEq0_sync1;
reg         PauseTimerEq0_sync2;
reg [15:0]  PauseTimer;
reg         Divider2;
reg  [5:0]  SlotTimer;
wire [47:0] ReservedMulticast;        
wire [15:0] TypeLength;               
wire        ResetByteCnt;             
wire        IncrementByteCnt;         
wire        ByteCntEq0;               
wire        ByteCntEq1;               
wire        ByteCntEq2;               
wire        ByteCntEq3;               
wire        ByteCntEq4;               
wire        ByteCntEq5;               
wire        ByteCntEq12;              
wire        ByteCntEq13;              
wire        ByteCntEq14;              
wire        ByteCntEq15;              
wire        ByteCntEq16;              
wire        ByteCntEq17;              
wire        ByteCntEq18;              
wire        DecrementPauseTimer;      
wire        PauseTimerEq0;            
wire        ResetSlotTimer;           
wire        IncrementSlotTimer;       
wire        SlotFinished;             
assign ReservedMulticast = 48'h0180C2000001;
assign TypeLength = 16'h8808;
always @ (posedge MRxClk or posedge RxReset)
begin
  if(RxReset)
    ref_AddressOK <=  1'b0;
  else
  if(DetectionWindow & ByteCntEq0)
    ref_AddressOK <=   RxData[7:0] == ReservedMulticast[47:40] | RxData[7:0] == MAC[47:40];
  else
  if(DetectionWindow & ByteCntEq1)
    ref_AddressOK <=  (RxData[7:0] == ReservedMulticast[39:32] | RxData[7:0] == MAC[39:32]) & ref_AddressOK;
  else
  if(DetectionWindow & ByteCntEq2)
    ref_AddressOK <=  (RxData[7:0] == ReservedMulticast[31:24] | RxData[7:0] == MAC[31:24]) & ref_AddressOK;
  else
  if(DetectionWindow & ByteCntEq3)
    ref_AddressOK <=  (RxData[7:0] == ReservedMulticast[23:16] | RxData[7:0] == MAC[23:16]) & ref_AddressOK;
  else
  if(DetectionWindow & ByteCntEq4)
    ref_AddressOK <=  (RxData[7:0] == ReservedMulticast[15:8]  | RxData[7:0] == MAC[15:8])  & ref_AddressOK;
  else
  if(DetectionWindow & ByteCntEq5)
    ref_AddressOK <=  (RxData[7:0] == ReservedMulticast[7:0]   | RxData[7:0] == MAC[7:0])   & ref_AddressOK;
  else
  if(ReceiveEnd)
    ref_AddressOK <=  1'b0;
end
always @ (posedge MRxClk or posedge RxReset )
begin
  if(RxReset)
    TypeLengthOK <=  1'b0;
  else
  if(DetectionWindow & ByteCntEq12)
    TypeLengthOK <=  ByteCntEq12 & (RxData[7:0] == TypeLength[15:8]);
  else
  if(DetectionWindow & ByteCntEq13)
    TypeLengthOK <=  ByteCntEq13 & (RxData[7:0] == TypeLength[7:0]) & TypeLengthOK;
  else
  if(ReceiveEnd)
    TypeLengthOK <=  1'b0;
end
always @ (posedge MRxClk or posedge RxReset )
begin
  if(RxReset)
    OpCodeOK <=  1'b0;
  else
  if(ByteCntEq16)
    OpCodeOK <=  1'b0;
  else
    begin
      if(DetectionWindow & ByteCntEq14)
        OpCodeOK <=  ByteCntEq14 & RxData[7:0] == 8'h00;
      if(DetectionWindow & ByteCntEq15)
        OpCodeOK <=  ByteCntEq15 & RxData[7:0] == 8'h01 & OpCodeOK;
    end
end
always @ (posedge MRxClk or posedge RxReset )
begin
  if(RxReset)
    ReceivedPauseFrmWAddr <=  1'b0;
  else
  if(ReceiveEnd)
    ReceivedPauseFrmWAddr <=  1'b0;
  else
  if(ByteCntEq16 & TypeLengthOK & OpCodeOK & ref_AddressOK)
    ReceivedPauseFrmWAddr <=  1'b1;        
end
always @ (posedge MRxClk or posedge RxReset )
begin
  if(RxReset)
    AssembledTimerValue[15:0] <=  16'h0;
  else
  if(RxStartFrm)
    AssembledTimerValue[15:0] <=  16'h0;
  else
    begin
      if(DetectionWindow & ByteCntEq16)
        AssembledTimerValue[15:8] <=  RxData[7:0];
      if(DetectionWindow & ByteCntEq17)
        AssembledTimerValue[7:0] <=  RxData[7:0];
    end
end
always @ (posedge MRxClk or posedge RxReset )
begin
  if(RxReset)
    DetectionWindow <=  1'b1;
  else
  if(ByteCntEq18)
    DetectionWindow <=  1'b0;
  else
  if(ReceiveEnd)
    DetectionWindow <=  1'b1;
end
always @ (posedge MRxClk or posedge RxReset )
begin
  if(RxReset)
    LatchedTimerValue[15:0] <=  16'h0;
  else
  if(DetectionWindow &  ReceivedPauseFrmWAddr &  ByteCntEq18)
    LatchedTimerValue[15:0] <=  AssembledTimerValue[15:0];
  else
  if(ReceiveEnd)
    LatchedTimerValue[15:0] <=  16'h0;
end
always @ (posedge MRxClk or posedge RxReset)
begin
  if(RxReset)
    DlyCrcCnt <=  3'h0;
  else
  if(RxValid & RxEndFrm)
    DlyCrcCnt <=  3'h0;
  else
  if(RxValid & ~RxEndFrm & ~DlyCrcCnt[2])
    DlyCrcCnt <=  DlyCrcCnt + 3'd1;
end
assign ResetByteCnt = RxEndFrm;
assign IncrementByteCnt = RxValid & DetectionWindow & ~ByteCntEq18 & 
			  (~DlyCrcEn | DlyCrcEn & DlyCrcCnt[2]);
always @ (posedge MRxClk or posedge RxReset)
begin
  if(RxReset)
    ByteCnt[4:0] <=  5'h0;
  else
  if(ResetByteCnt)
    ByteCnt[4:0] <=  5'h0;
  else
  if(IncrementByteCnt)
    ByteCnt[4:0] <=  ByteCnt[4:0] + 5'd1;
end
assign ByteCntEq0 = RxValid & ByteCnt[4:0] == 5'h0;
assign ByteCntEq1 = RxValid & ByteCnt[4:0] == 5'h1;
assign ByteCntEq2 = RxValid & ByteCnt[4:0] == 5'h2;
assign ByteCntEq3 = RxValid & ByteCnt[4:0] == 5'h3;
assign ByteCntEq4 = RxValid & ByteCnt[4:0] == 5'h4;
assign ByteCntEq5 = RxValid & ByteCnt[4:0] == 5'h5;
assign ByteCntEq12 = RxValid & ByteCnt[4:0] == 5'h0C;
assign ByteCntEq13 = RxValid & ByteCnt[4:0] == 5'h0D;
assign ByteCntEq14 = RxValid & ByteCnt[4:0] == 5'h0E;
assign ByteCntEq15 = RxValid & ByteCnt[4:0] == 5'h0F;
assign ByteCntEq16 = RxValid & ByteCnt[4:0] == 5'h10;
assign ByteCntEq17 = RxValid & ByteCnt[4:0] == 5'h11;
assign ByteCntEq18 = RxValid & ByteCnt[4:0] == 5'h12 & DetectionWindow;
assign ref_SetPauseTimer = ReceiveEnd & ReceivedPauseFrmWAddr & ReceivedPacketGood & ReceivedLengthOK & RxFlow;
assign DecrementPauseTimer = SlotFinished & |PauseTimer;
always @ (posedge MRxClk or posedge RxReset)
begin
  if(RxReset)
    PauseTimer[15:0] <=  16'h0;
  else
  if(ref_SetPauseTimer)
    PauseTimer[15:0] <=  LatchedTimerValue[15:0];
  else
  if(DecrementPauseTimer)
    PauseTimer[15:0] <=  PauseTimer[15:0] - 16'd1;
end
assign PauseTimerEq0 = ~(|PauseTimer[15:0]);
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    begin
      PauseTimerEq0_sync1 <=  1'b1;
      PauseTimerEq0_sync2 <=  1'b1;
    end
  else
    begin
      PauseTimerEq0_sync1 <=  PauseTimerEq0;
      PauseTimerEq0_sync2 <=  PauseTimerEq0_sync1;
    end
end
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    ref_Pause <=  1'b0;
  else
  if((TxDoneIn | TxAbortIn | ~TxUsedDataOutDetected) & ~TxStartFrmOut)
    ref_Pause <=  RxFlow & ~PauseTimerEq0_sync2;
end
always @ (posedge MRxClk or posedge RxReset)
begin
  if(RxReset)
    Divider2 <=  1'b0;
  else
  if(|PauseTimer[15:0] & RxFlow)
    Divider2 <=  ~Divider2;
  else
    Divider2 <=  1'b0;
end
assign ResetSlotTimer = RxReset;
assign IncrementSlotTimer =  ref_Pause & RxFlow & Divider2;
always @ (posedge MRxClk or posedge RxReset)
begin
  if(RxReset)
    SlotTimer[5:0] <=  6'h0;
  else
  if(ResetSlotTimer)
    SlotTimer[5:0] <=  6'h0;
  else
  if(IncrementSlotTimer)
    SlotTimer[5:0] <=  SlotTimer[5:0] + 6'd1;
end
assign SlotFinished = &SlotTimer[5:0] & IncrementSlotTimer;  
always @ (posedge MRxClk or posedge RxReset)
begin
  if(RxReset)
    ref_ReceivedPauseFrm <= 1'b0;
  else
  if(RxStatusWriteLatched_sync2 & r_PassAll | ref_ReceivedPauseFrm & (~r_PassAll))
    ref_ReceivedPauseFrm <= 1'b0;
  else
  if(ByteCntEq16 & TypeLengthOK & OpCodeOK)
    ref_ReceivedPauseFrm <= 1'b1;        
end
endmodule

