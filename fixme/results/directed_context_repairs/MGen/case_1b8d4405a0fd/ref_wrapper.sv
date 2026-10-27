`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned MTxClk,
    input longint unsigned MRxClk,
    input longint unsigned TxReset,
    input longint unsigned RxReset,
    input longint unsigned RxData,
    input longint unsigned RxValid,
    input longint unsigned RxStartFrm,
    input longint unsigned RxEndFrm,
    input longint unsigned RxFlow,
    input longint unsigned ReceiveEnd,
    input longint unsigned MAC,
    input longint unsigned DlyCrcEn,
    input longint unsigned TxDoneIn,
    input longint unsigned TxAbortIn,
    input longint unsigned TxStartFrmOut,
    input longint unsigned ReceivedLengthOK,
    input longint unsigned ReceivedPacketGood,
    input longint unsigned TxUsedDataOutDetected,
    output longint unsigned ref_Pause__dpi,
    output longint unsigned ref_ReceivedPauseFrm__dpi,
    output longint unsigned ref_AddressOK__dpi,
    input longint unsigned RxStatusWriteLatched_sync2,
    input longint unsigned r_PassAll,
    output longint unsigned ref_SetPauseTimer__dpi
);

module ref_eth_receivecontrol (
    MTxClk,
    MRxClk,
    TxReset,
    RxReset,
    RxData,
    RxValid,
    RxStartFrm,
    RxEndFrm,
    RxFlow,
    ReceiveEnd,
    MAC,
    DlyCrcEn,
    TxDoneIn,
    TxAbortIn,
    TxStartFrmOut,
    ReceivedLengthOK,
    ReceivedPacketGood,
    TxUsedDataOutDetected,
    ref_Pause,
    ref_ReceivedPauseFrm,
    ref_AddressOK,
    RxStatusWriteLatched_sync2,
    r_PassAll,
    ref_SetPauseTimer
);
input MTxClk;
input MRxClk;
input TxReset;
input RxReset;
input [7:0] RxData;
input RxValid;
input RxStartFrm;
input RxEndFrm;
input RxFlow;
input ReceiveEnd;
input [47:0] MAC;
input DlyCrcEn;
input TxDoneIn;
input TxAbortIn;
input TxStartFrmOut;
input ReceivedLengthOK;
input ReceivedPacketGood;
input TxUsedDataOutDetected;
output reg ref_Pause;
output reg ref_ReceivedPauseFrm;
output reg ref_AddressOK;
input RxStatusWriteLatched_sync2;
input r_PassAll;
output reg ref_SetPauseTimer;
longint unsigned ref_Pause__dpi;
longint unsigned ref_ReceivedPauseFrm__dpi;
longint unsigned ref_AddressOK__dpi;
longint unsigned ref_SetPauseTimer__dpi;

always @(*) begin
    ref_model_eval(MTxClk, MRxClk, TxReset, RxReset, RxData, RxValid, RxStartFrm, RxEndFrm, RxFlow, ReceiveEnd, MAC, DlyCrcEn, TxDoneIn, TxAbortIn, TxStartFrmOut, ReceivedLengthOK, ReceivedPacketGood, TxUsedDataOutDetected, ref_Pause__dpi, ref_ReceivedPauseFrm__dpi, ref_AddressOK__dpi, RxStatusWriteLatched_sync2, r_PassAll, ref_SetPauseTimer__dpi);
    ref_Pause = ref_Pause__dpi[0];
    ref_ReceivedPauseFrm = ref_ReceivedPauseFrm__dpi[0];
    ref_AddressOK = ref_AddressOK__dpi[0];
    ref_SetPauseTimer = ref_SetPauseTimer__dpi[0];
end
endmodule
