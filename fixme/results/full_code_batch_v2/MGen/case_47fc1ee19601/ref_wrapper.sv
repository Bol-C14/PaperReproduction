`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned i_d,
    input longint unsigned clk,
    input longint unsigned reset,
    output longint unsigned o_q__dpi,
    output longint unsigned o_qb__dpi
);

module dff_sync (
    i_d,
    clk,
    reset,
    o_q,
    o_qb
);
input i_d;
input clk;
input reset;
output reg o_q;
output reg o_qb;
longint unsigned o_q__dpi;
longint unsigned o_qb__dpi;

always @(*) begin
    ref_model_eval(i_d, clk, reset, o_q__dpi, o_qb__dpi);
    o_q = o_q__dpi[0];
    o_qb = o_qb__dpi[0];
end
endmodule
