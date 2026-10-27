`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned i_clk,
    input longint unsigned i_ce,
    input longint unsigned i_trigger,
    input longint unsigned i_data,
    input longint unsigned i_wb_clk,
    input longint unsigned i_wb_cyc,
    input longint unsigned i_wb_stb,
    input longint unsigned i_wb_we,
    input longint unsigned i_wb_addr,
    input longint unsigned i_wb_data,
    output longint unsigned ref_o_wb_ack__dpi,
    output longint unsigned ref_o_wb_stall__dpi,
    output longint unsigned ref_o_wb_data__dpi,
    output longint unsigned ref_o_interrupt__dpi
);

module ref_wbscope (
    i_clk,
    i_ce,
    i_trigger,
    i_data,
    i_wb_clk,
    i_wb_cyc,
    i_wb_stb,
    i_wb_we,
    i_wb_addr,
    i_wb_data,
    ref_o_wb_ack,
    ref_o_wb_stall,
    ref_o_wb_data,
    ref_o_interrupt
);
parameter LGMEM = 10;
parameter BUSW = 32;
input i_clk;
input i_ce;
input i_trigger;
input [31:0] i_data;
input i_wb_clk;
input i_wb_cyc;
input i_wb_stb;
input i_wb_we;
input i_wb_addr;
input [31:0] i_wb_data;
output reg ref_o_wb_ack;
output reg ref_o_wb_stall;
output reg [31:0] ref_o_wb_data;
output reg ref_o_interrupt;
longint unsigned ref_o_wb_ack__dpi;
longint unsigned ref_o_wb_stall__dpi;
longint unsigned ref_o_wb_data__dpi;
longint unsigned ref_o_interrupt__dpi;

always @(*) begin
    ref_model_eval(i_clk, i_ce, i_trigger, i_data, i_wb_clk, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data, ref_o_wb_ack__dpi, ref_o_wb_stall__dpi, ref_o_wb_data__dpi, ref_o_interrupt__dpi);
    ref_o_wb_ack = ref_o_wb_ack__dpi[0];
    ref_o_wb_stall = ref_o_wb_stall__dpi[0];
    ref_o_wb_data = ref_o_wb_data__dpi[31:0];
    ref_o_interrupt = ref_o_interrupt__dpi[0];
end
endmodule
