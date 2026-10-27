`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned rst_n,
    input longint unsigned ena,
    input longint unsigned t1s_sel,
    input longint unsigned prefix_sel,
    input longint unsigned suffix_sel,
    input longint unsigned calc_sel,
    input longint unsigned TrailingOnes,
    input longint unsigned TotalCoeff,
    input longint unsigned rbsp,
    input longint unsigned i,
    output longint unsigned ref_level_0__dpi,
    output longint unsigned ref_level_1__dpi,
    output longint unsigned ref_level_2__dpi,
    output longint unsigned ref_level_3__dpi,
    output longint unsigned ref_level_4__dpi,
    output longint unsigned ref_level_5__dpi,
    output longint unsigned ref_level_6__dpi,
    output longint unsigned ref_level_7__dpi,
    output longint unsigned ref_level_8__dpi,
    output longint unsigned ref_level_9__dpi,
    output longint unsigned ref_level_10__dpi,
    output longint unsigned ref_level_11__dpi,
    output longint unsigned ref_level_12__dpi,
    output longint unsigned ref_level_13__dpi,
    output longint unsigned ref_level_14__dpi,
    output longint unsigned ref_level_15__dpi,
    output longint unsigned ref_len_comb__dpi
);

module ref_cavlc_read_levels (
    clk,
    rst_n,
    ena,
    t1s_sel,
    prefix_sel,
    suffix_sel,
    calc_sel,
    TrailingOnes,
    TotalCoeff,
    rbsp,
    i,
    ref_level_0,
    ref_level_1,
    ref_level_2,
    ref_level_3,
    ref_level_4,
    ref_level_5,
    ref_level_6,
    ref_level_7,
    ref_level_8,
    ref_level_9,
    ref_level_10,
    ref_level_11,
    ref_level_12,
    ref_level_13,
    ref_level_14,
    ref_level_15,
    ref_len_comb
);
input clk;
input rst_n;
input ena;
input t1s_sel;
input prefix_sel;
input suffix_sel;
input calc_sel;
input [1:0] TrailingOnes;
input [4:0] TotalCoeff;
input [15:0] rbsp;
input [3:0] i;
output reg [8:0] ref_level_0;
output reg [8:0] ref_level_1;
output reg [8:0] ref_level_2;
output reg [8:0] ref_level_3;
output reg [8:0] ref_level_4;
output reg [8:0] ref_level_5;
output reg [8:0] ref_level_6;
output reg [8:0] ref_level_7;
output reg [8:0] ref_level_8;
output reg [8:0] ref_level_9;
output reg [8:0] ref_level_10;
output reg [8:0] ref_level_11;
output reg [8:0] ref_level_12;
output reg [8:0] ref_level_13;
output reg [8:0] ref_level_14;
output reg [8:0] ref_level_15;
output reg [4:0] ref_len_comb;
longint unsigned ref_level_0__dpi;
longint unsigned ref_level_1__dpi;
longint unsigned ref_level_2__dpi;
longint unsigned ref_level_3__dpi;
longint unsigned ref_level_4__dpi;
longint unsigned ref_level_5__dpi;
longint unsigned ref_level_6__dpi;
longint unsigned ref_level_7__dpi;
longint unsigned ref_level_8__dpi;
longint unsigned ref_level_9__dpi;
longint unsigned ref_level_10__dpi;
longint unsigned ref_level_11__dpi;
longint unsigned ref_level_12__dpi;
longint unsigned ref_level_13__dpi;
longint unsigned ref_level_14__dpi;
longint unsigned ref_level_15__dpi;
longint unsigned ref_len_comb__dpi;

always @(*) begin
    ref_model_eval(clk, rst_n, ena, t1s_sel, prefix_sel, suffix_sel, calc_sel, TrailingOnes, TotalCoeff, rbsp, i, ref_level_0__dpi, ref_level_1__dpi, ref_level_2__dpi, ref_level_3__dpi, ref_level_4__dpi, ref_level_5__dpi, ref_level_6__dpi, ref_level_7__dpi, ref_level_8__dpi, ref_level_9__dpi, ref_level_10__dpi, ref_level_11__dpi, ref_level_12__dpi, ref_level_13__dpi, ref_level_14__dpi, ref_level_15__dpi, ref_len_comb__dpi);
    ref_level_0 = ref_level_0__dpi[8:0];
    ref_level_1 = ref_level_1__dpi[8:0];
    ref_level_2 = ref_level_2__dpi[8:0];
    ref_level_3 = ref_level_3__dpi[8:0];
    ref_level_4 = ref_level_4__dpi[8:0];
    ref_level_5 = ref_level_5__dpi[8:0];
    ref_level_6 = ref_level_6__dpi[8:0];
    ref_level_7 = ref_level_7__dpi[8:0];
    ref_level_8 = ref_level_8__dpi[8:0];
    ref_level_9 = ref_level_9__dpi[8:0];
    ref_level_10 = ref_level_10__dpi[8:0];
    ref_level_11 = ref_level_11__dpi[8:0];
    ref_level_12 = ref_level_12__dpi[8:0];
    ref_level_13 = ref_level_13__dpi[8:0];
    ref_level_14 = ref_level_14__dpi[8:0];
    ref_level_15 = ref_level_15__dpi[8:0];
    ref_len_comb = ref_len_comb__dpi[4:0];
end
endmodule
