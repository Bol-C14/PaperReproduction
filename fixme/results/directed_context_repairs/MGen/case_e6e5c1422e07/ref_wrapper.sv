`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    output longint unsigned nmi_evt_ref__dpi,
    output longint unsigned per_dout_ref__dpi,
    output longint unsigned wdtifg_set_ref__dpi,
    output longint unsigned wdtpw_error_ref__dpi,
    output longint unsigned wdttmsel_ref__dpi,
    input longint unsigned aclk_en,
    input longint unsigned dbg_freeze,
    input longint unsigned mclk,
    input longint unsigned nmi,
    input longint unsigned nmie,
    input longint unsigned per_addr,
    input longint unsigned per_din,
    input longint unsigned per_en,
    input longint unsigned per_wen,
    input longint unsigned puc,
    input longint unsigned smclk_en
);

module omsp_watchdog_ref (
    nmi_evt_ref,
    per_dout_ref,
    wdtifg_set_ref,
    wdtpw_error_ref,
    wdttmsel_ref,
    aclk_en,
    dbg_freeze,
    mclk,
    nmi,
    nmie,
    per_addr,
    per_din,
    per_en,
    per_wen,
    puc,
    smclk_en
);
output reg nmi_evt_ref;
output reg [15:0] per_dout_ref;
output reg wdtifg_set_ref;
output reg wdtpw_error_ref;
output reg wdttmsel_ref;
input aclk_en;
input dbg_freeze;
input mclk;
input nmi;
input nmie;
input [7:0] per_addr;
input [15:0] per_din;
input per_en;
input [1:0] per_wen;
input puc;
input smclk_en;
longint unsigned nmi_evt_ref__dpi;
longint unsigned per_dout_ref__dpi;
longint unsigned wdtifg_set_ref__dpi;
longint unsigned wdtpw_error_ref__dpi;
longint unsigned wdttmsel_ref__dpi;

always @(*) begin
    ref_model_eval(nmi_evt_ref__dpi, per_dout_ref__dpi, wdtifg_set_ref__dpi, wdtpw_error_ref__dpi, wdttmsel_ref__dpi, aclk_en, dbg_freeze, mclk, nmi, nmie, per_addr, per_din, per_en, per_wen, puc, smclk_en);
    nmi_evt_ref = nmi_evt_ref__dpi[0];
    per_dout_ref = per_dout_ref__dpi[15:0];
    wdtifg_set_ref = wdtifg_set_ref__dpi[0];
    wdtpw_error_ref = wdtpw_error_ref__dpi[0];
    wdttmsel_ref = wdttmsel_ref__dpi[0];
end
endmodule
