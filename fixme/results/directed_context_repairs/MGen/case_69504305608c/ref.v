`timescale 1ns/1ps
 
module ref_eth_transmitcontrol (MTxClk, TxReset, TxUsedDataIn, TxUsedDataOut, TxDoneIn, TxAbortIn, 
                            TxStartFrmIn, TPauseRq, TxUsedDataOutDetected, TxFlow, DlyCrcEn, 
                            TxPauseTV, MAC, ref_TxCtrlStartFrm, ref_TxCtrlEndFrm, ref_SendingCtrlFrm, ref_CtrlMux, 
                            ref_ControlData, ref_WillSendControlFrame, ref_BlockTxDone
                           );
input         MTxClk;
input         TxReset;
input         TxUsedDataIn;
input         TxUsedDataOut;
input         TxDoneIn;
input         TxAbortIn;
input         TxStartFrmIn;
input         TPauseRq;
input         TxUsedDataOutDetected;
input         TxFlow;
input         DlyCrcEn;
input  [15:0] TxPauseTV;
input  [47:0] MAC;
output        ref_TxCtrlStartFrm;
output        ref_TxCtrlEndFrm;
output        ref_SendingCtrlFrm;
output        ref_CtrlMux;
output [7:0]  ref_ControlData;
output        ref_WillSendControlFrame;
output        ref_BlockTxDone;
reg           ref_SendingCtrlFrm;
reg           ref_CtrlMux;
reg           ref_WillSendControlFrame;
reg    [3:0]  DlyCrcCnt;
reg    [5:0]  ByteCnt;
reg           ControlEnd_q;
reg    [7:0]  MuxedCtrlData;
reg           ref_TxCtrlStartFrm;
reg           ref_TxCtrlStartFrm_q;
reg           ref_TxCtrlEndFrm;
reg    [7:0]  ref_ControlData;
reg           TxUsedDataIn_q;
reg           ref_BlockTxDone;
wire          IncrementDlyCrcCnt;
wire          ResetByteCnt;
wire          IncrementByteCnt;
wire          ControlEnd;
wire          IncrementByteCntBy2;
wire          EnableCnt;
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    ref_WillSendControlFrame <=  1'b0;
  else
  if(ref_TxCtrlEndFrm & ref_CtrlMux)
    ref_WillSendControlFrame <=  1'b0;
  else
  if(TPauseRq & TxFlow)
    ref_WillSendControlFrame <=  1'b1;
end
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    ref_TxCtrlStartFrm <=  1'b0;
  else
  if(TxUsedDataIn_q & ref_CtrlMux)
    ref_TxCtrlStartFrm <=  1'b0;
  else
  if(ref_WillSendControlFrame & ~TxUsedDataOut & (TxDoneIn | TxAbortIn | TxStartFrmIn | (~TxUsedDataOutDetected)))
    ref_TxCtrlStartFrm <=  1'b1;
end
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    ref_TxCtrlEndFrm <=  1'b0;
  else
  if(ControlEnd | ControlEnd_q)
    ref_TxCtrlEndFrm <=  1'b1;
  else
    ref_TxCtrlEndFrm <=  1'b0;
end
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    ref_CtrlMux <=  1'b0;
  else
  if(ref_WillSendControlFrame & ~TxUsedDataOut)
    ref_CtrlMux <=  1'b1;
  else
  if(TxDoneIn)
    ref_CtrlMux <=  1'b0;
end
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    ref_SendingCtrlFrm <=  1'b0;
  else
  if(ref_WillSendControlFrame & ref_TxCtrlStartFrm)
    ref_SendingCtrlFrm <=  1'b1;
  else
  if(TxDoneIn)
    ref_SendingCtrlFrm <=  1'b0;
end
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    TxUsedDataIn_q <=  1'b0;
  else
    TxUsedDataIn_q <=  TxUsedDataIn;
end
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    ref_BlockTxDone <=  1'b0;
  else
  if(ref_TxCtrlStartFrm)
    ref_BlockTxDone <=  1'b1;
  else
  if(TxStartFrmIn)
    ref_BlockTxDone <=  1'b0;
end
always @ (posedge MTxClk)
begin
  ControlEnd_q     <=  ControlEnd;
  ref_TxCtrlStartFrm_q <=  ref_TxCtrlStartFrm;
end
assign IncrementDlyCrcCnt = ref_CtrlMux & TxUsedDataIn &  ~DlyCrcCnt[2];
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    DlyCrcCnt <=  4'h0;
  else
  if(ResetByteCnt)
    DlyCrcCnt <=  4'h0;
  else
  if(IncrementDlyCrcCnt)
    DlyCrcCnt <=  DlyCrcCnt + 4'd1;
end
assign ResetByteCnt = TxReset | (~ref_TxCtrlStartFrm & (TxDoneIn | TxAbortIn));
assign IncrementByteCnt = ref_CtrlMux & (ref_TxCtrlStartFrm & ~ref_TxCtrlStartFrm_q & ~TxUsedDataIn | TxUsedDataIn & ~ControlEnd);
assign IncrementByteCntBy2 = ref_CtrlMux & ref_TxCtrlStartFrm & (~ref_TxCtrlStartFrm_q) & TxUsedDataIn;     
assign EnableCnt = (~DlyCrcEn | DlyCrcEn & (&DlyCrcCnt[1:0]));
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    ByteCnt <=  6'h0;
  else
  if(ResetByteCnt)
    ByteCnt <=  6'h0;
  else
  if(IncrementByteCntBy2 & EnableCnt)
    ByteCnt <=  (ByteCnt[5:0] ) + 6'd2;
  else
  if(IncrementByteCnt & EnableCnt)
    ByteCnt <=  (ByteCnt[5:0] ) + 6'd1;
end
assign ControlEnd = ByteCnt[5:0] == 6'h22;
always @ (ByteCnt or DlyCrcEn or MAC or TxPauseTV or DlyCrcCnt)
begin
  case(ByteCnt)
    6'h0:    if(~DlyCrcEn | DlyCrcEn & (&DlyCrcCnt[1:0]))
               MuxedCtrlData[7:0] = 8'h01;                   
             else
						 	 MuxedCtrlData[7:0] = 8'h0;
    6'h2:      MuxedCtrlData[7:0] = 8'h80;
    6'h4:      MuxedCtrlData[7:0] = 8'hC2;
    6'h6:      MuxedCtrlData[7:0] = 8'h00;
    6'h8:      MuxedCtrlData[7:0] = 8'h00;
    6'hA:      MuxedCtrlData[7:0] = 8'h01;
    6'hC:      MuxedCtrlData[7:0] = MAC[47:40];
    6'hE:      MuxedCtrlData[7:0] = MAC[39:32];
    6'h10:     MuxedCtrlData[7:0] = MAC[31:24];
    6'h12:     MuxedCtrlData[7:0] = MAC[23:16];
    6'h14:     MuxedCtrlData[7:0] = MAC[15:8];
    6'h16:     MuxedCtrlData[7:0] = MAC[7:0];
    6'h18:     MuxedCtrlData[7:0] = 8'h88;                   
    6'h1A:     MuxedCtrlData[7:0] = 8'h08;
    6'h1C:     MuxedCtrlData[7:0] = 8'h00;                   
    6'h1E:     MuxedCtrlData[7:0] = 8'h01;
    6'h20:     MuxedCtrlData[7:0] = TxPauseTV[15:8];         
    6'h22:     MuxedCtrlData[7:0] = TxPauseTV[7:0];
    default:   MuxedCtrlData[7:0] = 8'h0;
  endcase
end
always @ (posedge MTxClk or posedge TxReset)
begin
  if(TxReset)
    ref_ControlData[7:0] <=  8'h0;
  else
  if(~ByteCnt[0])
    ref_ControlData[7:0] <=  MuxedCtrlData[7:0];
end
endmodule

