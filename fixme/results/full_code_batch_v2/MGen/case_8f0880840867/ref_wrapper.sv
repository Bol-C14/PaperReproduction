`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned wclk,
    input longint unsigned wrst_n,
    input longint unsigned wen,
    output longint unsigned wfull_ref__dpi,
    output longint unsigned walmost_full_ref__dpi,
    output longint unsigned mem_wen_ref__dpi,
    output longint unsigned mem_waddr_ref__dpi,
    input longint unsigned rclk,
    input longint unsigned rrst_n,
    input longint unsigned ren,
    output longint unsigned rempty_ref__dpi,
    output longint unsigned ralmost_empty_ref__dpi,
    output longint unsigned mem_ren_ref__dpi,
    output longint unsigned mem_raddr_ref__dpi
);

module generic_fifo_ctrl_ref (
    wclk,
    wrst_n,
    wen,
    wfull_ref,
    walmost_full_ref,
    mem_wen_ref,
    mem_waddr_ref,
    rclk,
    rrst_n,
    ren,
    rempty_ref,
    ralmost_empty_ref,
    mem_ren_ref,
    mem_raddr_ref
);
parameter AWIDTH = 3;
parameter RAM_DEPTH = 8;
parameter ALMOST_EMPTY_THRESH = 1;
parameter ALMOST_FULL_THRESH = 6;
input wclk;
input wrst_n;
input wen;
output reg wfull_ref;
output reg walmost_full_ref;
output reg mem_wen_ref;
output reg [3:0] mem_waddr_ref;
input rclk;
input rrst_n;
input ren;
output reg rempty_ref;
output reg ralmost_empty_ref;
output reg mem_ren_ref;
output reg [3:0] mem_raddr_ref;
longint unsigned wfull_ref__dpi;
longint unsigned walmost_full_ref__dpi;
longint unsigned mem_wen_ref__dpi;
longint unsigned mem_waddr_ref__dpi;
longint unsigned rempty_ref__dpi;
longint unsigned ralmost_empty_ref__dpi;
longint unsigned mem_ren_ref__dpi;
longint unsigned mem_raddr_ref__dpi;

always @(*) begin
    ref_model_eval(wclk, wrst_n, wen, wfull_ref__dpi, walmost_full_ref__dpi, mem_wen_ref__dpi, mem_waddr_ref__dpi, rclk, rrst_n, ren, rempty_ref__dpi, ralmost_empty_ref__dpi, mem_ren_ref__dpi, mem_raddr_ref__dpi);
    wfull_ref = wfull_ref__dpi[0];
    walmost_full_ref = walmost_full_ref__dpi[0];
    mem_wen_ref = mem_wen_ref__dpi[0];
    mem_waddr_ref = mem_waddr_ref__dpi[3:0];
    rempty_ref = rempty_ref__dpi[0];
    ralmost_empty_ref = ralmost_empty_ref__dpi[0];
    mem_ren_ref = mem_ren_ref__dpi[0];
    mem_raddr_ref = mem_raddr_ref__dpi[3:0];
end
endmodule
