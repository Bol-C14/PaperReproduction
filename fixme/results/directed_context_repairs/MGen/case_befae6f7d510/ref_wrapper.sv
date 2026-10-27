`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned i_data_clk,
    input longint unsigned i_ce,
    input longint unsigned i_trigger,
    input longint unsigned i_data,
    input longint unsigned i_wb_clk,
    input longint unsigned i_wb_cyc,
    input longint unsigned i_wb_stb,
    input longint unsigned i_wb_we,
    input longint unsigned i_wb_addr,
    input longint unsigned i_wb_data,
    output longint unsigned o_wb_ack_ref__dpi,
    output longint unsigned o_wb_stall_ref__dpi,
    output longint unsigned o_wb_data_ref__dpi,
    output longint unsigned o_interrupt_ref__dpi
);

module wbscopc_ref (
    i_data_clk,
    i_ce,
    i_trigger,
    i_data,
    i_wb_clk,
    i_wb_cyc,
    i_wb_stb,
    i_wb_we,
    i_wb_addr,
    i_wb_data,
    o_wb_ack_ref,
    o_wb_stall_ref,
    o_wb_data_ref,
    o_interrupt_ref
);
input i_data_clk;
input i_ce;
input i_trigger;
input [30:0] i_data;
input i_wb_clk;
input i_wb_cyc;
input i_wb_stb;
input i_wb_we;
input i_wb_addr;
input [31:0] i_wb_data;
output reg o_wb_ack_ref;
output reg o_wb_stall_ref;
output reg [31:0] o_wb_data_ref;
output reg o_interrupt_ref;
longint unsigned o_wb_ack_ref__dpi;
longint unsigned o_wb_stall_ref__dpi;
longint unsigned o_wb_data_ref__dpi;
longint unsigned o_interrupt_ref__dpi;

always @(*) begin
    ref_model_eval(i_data_clk, i_ce, i_trigger, i_data, i_wb_clk, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data, o_wb_ack_ref__dpi, o_wb_stall_ref__dpi, o_wb_data_ref__dpi, o_interrupt_ref__dpi);
    o_wb_ack_ref = o_wb_ack_ref__dpi[0];
    o_wb_stall_ref = o_wb_stall_ref__dpi[0];
    o_wb_data_ref = o_wb_data_ref__dpi[31:0];
    o_interrupt_ref = o_interrupt_ref__dpi[0];
end
endmodule
