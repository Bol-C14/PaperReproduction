`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned i_clk,
    input longint unsigned i_wb_cyc,
    input longint unsigned i_wb_stb,
    input longint unsigned i_wb_we,
    input longint unsigned i_wb_addr,
    input longint unsigned i_wb_data,
    output longint unsigned ref_o_data__dpi,
    output longint unsigned ref_o_interrupt__dpi,
    output longint unsigned ref_o_ppd__dpi
);

module ref_rtclight (
    i_clk,
    i_wb_cyc,
    i_wb_stb,
    i_wb_we,
    i_wb_addr,
    i_wb_data,
    ref_o_data,
    ref_o_interrupt,
    ref_o_ppd
);
input i_clk;
input i_wb_cyc;
input i_wb_stb;
input i_wb_we;
input [2:0] i_wb_addr;
input [31:0] i_wb_data;
output reg [31:0] ref_o_data;
output reg ref_o_interrupt;
output reg ref_o_ppd;
longint unsigned ref_o_data__dpi;
longint unsigned ref_o_interrupt__dpi;
longint unsigned ref_o_ppd__dpi;

always @(*) begin
    ref_model_eval(i_clk, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data, ref_o_data__dpi, ref_o_interrupt__dpi, ref_o_ppd__dpi);
    ref_o_data = ref_o_data__dpi[31:0];
    ref_o_interrupt = ref_o_interrupt__dpi[0];
    ref_o_ppd = ref_o_ppd__dpi[0];
end
endmodule
