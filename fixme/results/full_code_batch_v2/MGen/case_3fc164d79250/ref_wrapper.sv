`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned DP_Hazards,
    input longint unsigned ID_Rs,
    input longint unsigned ID_Rt,
    input longint unsigned EX_Rs,
    input longint unsigned EX_Rt,
    input longint unsigned EX_RtRd,
    input longint unsigned MEM_RtRd,
    input longint unsigned WB_RtRd,
    input longint unsigned EX_Link,
    input longint unsigned EX_RegWrite,
    input longint unsigned MEM_RegWrite,
    input longint unsigned WB_RegWrite,
    input longint unsigned MEM_MemRead,
    input longint unsigned MEM_MemWrite,
    input longint unsigned InstMem_Read,
    input longint unsigned InstMem_Ready,
    input longint unsigned Mfc0,
    input longint unsigned IF_Exception_Stall,
    input longint unsigned ID_Exception_Stall,
    input longint unsigned EX_Exception_Stall,
    input longint unsigned EX_ALU_Stall,
    input longint unsigned M_Stall_Controller,
    output longint unsigned IF_Stall_ref__dpi,
    output longint unsigned ID_Stall_ref__dpi,
    output longint unsigned EX_Stall_ref__dpi,
    output longint unsigned M_Stall_ref__dpi,
    output longint unsigned WB_Stall_ref__dpi,
    output longint unsigned ID_RsFwdSel_ref__dpi,
    output longint unsigned ID_RtFwdSel_ref__dpi,
    output longint unsigned EX_RsFwdSel_ref__dpi,
    output longint unsigned EX_RtFwdSel_ref__dpi,
    output longint unsigned M_WriteDataFwdSel_ref__dpi
);

module Hazard_Detection_ref (
    DP_Hazards,
    ID_Rs,
    ID_Rt,
    EX_Rs,
    EX_Rt,
    EX_RtRd,
    MEM_RtRd,
    WB_RtRd,
    EX_Link,
    EX_RegWrite,
    MEM_RegWrite,
    WB_RegWrite,
    MEM_MemRead,
    MEM_MemWrite,
    InstMem_Read,
    InstMem_Ready,
    Mfc0,
    IF_Exception_Stall,
    ID_Exception_Stall,
    EX_Exception_Stall,
    EX_ALU_Stall,
    M_Stall_Controller,
    IF_Stall_ref,
    ID_Stall_ref,
    EX_Stall_ref,
    M_Stall_ref,
    WB_Stall_ref,
    ID_RsFwdSel_ref,
    ID_RtFwdSel_ref,
    EX_RsFwdSel_ref,
    EX_RtFwdSel_ref,
    M_WriteDataFwdSel_ref
);
input [7:0] DP_Hazards;
input [4:0] ID_Rs;
input [4:0] ID_Rt;
input [4:0] EX_Rs;
input [4:0] EX_Rt;
input [4:0] EX_RtRd;
input [4:0] MEM_RtRd;
input [4:0] WB_RtRd;
input EX_Link;
input EX_RegWrite;
input MEM_RegWrite;
input WB_RegWrite;
input MEM_MemRead;
input MEM_MemWrite;
input InstMem_Read;
input InstMem_Ready;
input Mfc0;
input IF_Exception_Stall;
input ID_Exception_Stall;
input EX_Exception_Stall;
input EX_ALU_Stall;
input M_Stall_Controller;
output reg IF_Stall_ref;
output reg ID_Stall_ref;
output reg EX_Stall_ref;
output reg M_Stall_ref;
output reg WB_Stall_ref;
output reg [1:0] ID_RsFwdSel_ref;
output reg [1:0] ID_RtFwdSel_ref;
output reg [1:0] EX_RsFwdSel_ref;
output reg [1:0] EX_RtFwdSel_ref;
output reg M_WriteDataFwdSel_ref;
longint unsigned IF_Stall_ref__dpi;
longint unsigned ID_Stall_ref__dpi;
longint unsigned EX_Stall_ref__dpi;
longint unsigned M_Stall_ref__dpi;
longint unsigned WB_Stall_ref__dpi;
longint unsigned ID_RsFwdSel_ref__dpi;
longint unsigned ID_RtFwdSel_ref__dpi;
longint unsigned EX_RsFwdSel_ref__dpi;
longint unsigned EX_RtFwdSel_ref__dpi;
longint unsigned M_WriteDataFwdSel_ref__dpi;

always @(*) begin
    ref_model_eval(DP_Hazards, ID_Rs, ID_Rt, EX_Rs, EX_Rt, EX_RtRd, MEM_RtRd, WB_RtRd, EX_Link, EX_RegWrite, MEM_RegWrite, WB_RegWrite, MEM_MemRead, MEM_MemWrite, InstMem_Read, InstMem_Ready, Mfc0, IF_Exception_Stall, ID_Exception_Stall, EX_Exception_Stall, EX_ALU_Stall, M_Stall_Controller, IF_Stall_ref__dpi, ID_Stall_ref__dpi, EX_Stall_ref__dpi, M_Stall_ref__dpi, WB_Stall_ref__dpi, ID_RsFwdSel_ref__dpi, ID_RtFwdSel_ref__dpi, EX_RsFwdSel_ref__dpi, EX_RtFwdSel_ref__dpi, M_WriteDataFwdSel_ref__dpi);
    IF_Stall_ref = IF_Stall_ref__dpi[0];
    ID_Stall_ref = ID_Stall_ref__dpi[0];
    EX_Stall_ref = EX_Stall_ref__dpi[0];
    M_Stall_ref = M_Stall_ref__dpi[0];
    WB_Stall_ref = WB_Stall_ref__dpi[0];
    ID_RsFwdSel_ref = ID_RsFwdSel_ref__dpi[1:0];
    ID_RtFwdSel_ref = ID_RtFwdSel_ref__dpi[1:0];
    EX_RsFwdSel_ref = EX_RsFwdSel_ref__dpi[1:0];
    EX_RtFwdSel_ref = EX_RtFwdSel_ref__dpi[1:0];
    M_WriteDataFwdSel_ref = M_WriteDataFwdSel_ref__dpi[0];
end
endmodule
