`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned rst_n,
    input longint unsigned in_m,
    output longint unsigned goods_ref__dpi,
    output longint unsigned out_m_ref__dpi
);

module FSM_ref (
    clk,
    rst_n,
    in_m,
    goods_ref,
    out_m_ref
);
input clk;
input rst_n;
input [3:0] in_m;
output reg goods_ref;
output reg [3:0] out_m_ref;
longint unsigned goods_ref__dpi;
longint unsigned out_m_ref__dpi;

always @(*) begin
    ref_model_eval(clk, rst_n, in_m, goods_ref__dpi, out_m_ref__dpi);
    goods_ref = goods_ref__dpi[0];
    out_m_ref = out_m_ref__dpi[3:0];
end
endmodule
