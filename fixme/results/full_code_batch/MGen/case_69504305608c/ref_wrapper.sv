`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned MTxClk,
    input longint unsigned TxReset,
    input longint unsigned TxUsedDataIn,
    input longint unsigned TxUsedDataOut,
    input longint unsigned TxDoneIn,
    input longint unsigned TxAbortIn,
    input longint unsigned TxStartFrmIn,
    input longint unsigned TPauseRq,
    input longint unsigned TxUsedDataOutDetected,
    input longint unsigned TxFlow,
    input longint unsigned DlyCrcEn,
    input longint unsigned TxPauseTV,
    input longint unsigned MAC,
    output longint unsigned ref_TxCtrlStartFrm__dpi,
    output longint unsigned ref_TxCtrlEndFrm__dpi,
    output longint unsigned ref_SendingCtrlFrm__dpi,
    output longint unsigned ref_CtrlMux__dpi,
    output longint unsigned ref_ControlData__dpi,
    output longint unsigned ref_WillSendControlFrame__dpi,
    output longint unsigned ref_BlockTxDone__dpi
);

module ref_eth_transmitcontrol (
    MTxClk,
    TxReset,
    TxUsedDataIn,
    TxUsedDataOut,
    TxDoneIn,
    TxAbortIn,
    TxStartFrmIn,
    TPauseRq,
    TxUsedDataOutDetected,
    TxFlow,
    DlyCrcEn,
    TxPauseTV,
    MAC,
    ref_TxCtrlStartFrm,
    ref_TxCtrlEndFrm,
    ref_SendingCtrlFrm,
    ref_CtrlMux,
    ref_ControlData,
    ref_WillSendControlFrame,
    ref_BlockTxDone
);
input MTxClk;
input TxReset;
input TxUsedDataIn;
input TxUsedDataOut;
input TxDoneIn;
input TxAbortIn;
input TxStartFrmIn;
input TPauseRq;
input TxUsedDataOutDetected;
input TxFlow;
input DlyCrcEn;
input [15:0] TxPauseTV;
input [47:0] MAC;
output reg ref_TxCtrlStartFrm;
output reg ref_TxCtrlEndFrm;
output reg ref_SendingCtrlFrm;
output reg ref_CtrlMux;
output reg [7:0] ref_ControlData;
output reg ref_WillSendControlFrame;
output reg ref_BlockTxDone;
longint unsigned ref_TxCtrlStartFrm__dpi;
longint unsigned ref_TxCtrlEndFrm__dpi;
longint unsigned ref_SendingCtrlFrm__dpi;
longint unsigned ref_CtrlMux__dpi;
longint unsigned ref_ControlData__dpi;
longint unsigned ref_WillSendControlFrame__dpi;
longint unsigned ref_BlockTxDone__dpi;

always @(*) begin
    ref_model_eval(MTxClk, TxReset, TxUsedDataIn, TxUsedDataOut, TxDoneIn, TxAbortIn, TxStartFrmIn, TPauseRq, TxUsedDataOutDetected, TxFlow, DlyCrcEn, TxPauseTV, MAC, ref_TxCtrlStartFrm__dpi, ref_TxCtrlEndFrm__dpi, ref_SendingCtrlFrm__dpi, ref_CtrlMux__dpi, ref_ControlData__dpi, ref_WillSendControlFrame__dpi, ref_BlockTxDone__dpi);
    ref_TxCtrlStartFrm = ref_TxCtrlStartFrm__dpi[0];
    ref_TxCtrlEndFrm = ref_TxCtrlEndFrm__dpi[0];
    ref_SendingCtrlFrm = ref_SendingCtrlFrm__dpi[0];
    ref_CtrlMux = ref_CtrlMux__dpi[0];
    ref_ControlData = ref_ControlData__dpi[7:0];
    ref_WillSendControlFrame = ref_WillSendControlFrame__dpi[0];
    ref_BlockTxDone = ref_BlockTxDone__dpi[0];
end
endmodule
