`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned reset,
    input longint unsigned Sm1,
    input longint unsigned Sm9,
    input longint unsigned Sm_ready,
    input longint unsigned erasure_ready,
    input longint unsigned erasure_cnt,
    input longint unsigned pow1,
    input longint unsigned dec1,
    output longint unsigned ref_add_pow1__dpi,
    output longint unsigned ref_add_dec1__dpi,
    output longint unsigned ref_L_ready__dpi,
    output longint unsigned ref_L1__dpi
);

module ref_BM_lamda (
    clk,
    reset,
    Sm1,
    Sm9,
    Sm_ready,
    erasure_ready,
    erasure_cnt,
    pow1,
    dec1,
    ref_add_pow1,
    ref_add_dec1,
    ref_L_ready,
    ref_L1
);
input clk;
input reset;
input [7:0] Sm1;
input [7:0] Sm9;
input Sm_ready;
input erasure_ready;
input [3:0] erasure_cnt;
input [7:0] pow1;
input [7:0] dec1;
output reg [7:0] ref_add_pow1;
output reg [7:0] ref_add_dec1;
output reg ref_L_ready;
output reg [7:0] ref_L1;
longint unsigned ref_add_pow1__dpi;
longint unsigned ref_add_dec1__dpi;
longint unsigned ref_L_ready__dpi;
longint unsigned ref_L1__dpi;

always @(*) begin
    ref_model_eval(clk, reset, Sm1, Sm9, Sm_ready, erasure_ready, erasure_cnt, pow1, dec1, ref_add_pow1__dpi, ref_add_dec1__dpi, ref_L_ready__dpi, ref_L1__dpi);
    ref_add_pow1 = ref_add_pow1__dpi[7:0];
    ref_add_dec1 = ref_add_dec1__dpi[7:0];
    ref_L_ready = ref_L_ready__dpi[0];
    ref_L1 = ref_L1__dpi[7:0];
end
endmodule
