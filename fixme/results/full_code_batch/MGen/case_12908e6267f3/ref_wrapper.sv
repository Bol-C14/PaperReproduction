`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned rst,
    input longint unsigned enable,
    input longint unsigned selection,
    input longint unsigned d_in_0,
    input longint unsigned d_in_1,
    output longint unsigned ref_d_o__dpi,
    output longint unsigned ref_wr_en__dpi
);

module ref_tbu (
    clk,
    rst,
    enable,
    selection,
    d_in_0,
    d_in_1,
    ref_d_o,
    ref_wr_en
);
input clk;
input rst;
input enable;
input selection;
input [7:0] d_in_0;
input [7:0] d_in_1;
output reg ref_d_o;
output reg ref_wr_en;
longint unsigned ref_d_o__dpi;
longint unsigned ref_wr_en__dpi;

always @(*) begin
    ref_model_eval(clk, rst, enable, selection, d_in_0, d_in_1, ref_d_o__dpi, ref_wr_en__dpi);
    ref_d_o = ref_d_o__dpi[0];
    ref_wr_en = ref_wr_en__dpi[0];
end
endmodule
