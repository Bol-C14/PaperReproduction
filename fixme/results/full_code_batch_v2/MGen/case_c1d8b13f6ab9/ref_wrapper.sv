`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned i_clk,
    input longint unsigned i_rst,
    input longint unsigned i_ce,
    input longint unsigned i_stalled_n,
    input longint unsigned i_pc,
    input longint unsigned i_aux,
    output longint unsigned o_i_ref__dpi,
    output longint unsigned o_pc_ref__dpi,
    output longint unsigned o_aux_ref__dpi,
    output longint unsigned o_valid_ref__dpi,
    output longint unsigned o_illegal_ref__dpi,
    output longint unsigned o_wb_cyc_ref__dpi,
    output longint unsigned o_wb_stb_ref__dpi,
    output longint unsigned o_wb_we_ref__dpi,
    output longint unsigned o_wb_addr_ref__dpi,
    output longint unsigned o_wb_data_ref__dpi,
    input longint unsigned i_wb_ack,
    input longint unsigned i_wb_stall,
    input longint unsigned i_wb_err,
    input longint unsigned i_wb_data
);

module prefetch_ref (
    i_clk,
    i_rst,
    i_ce,
    i_stalled_n,
    i_pc,
    i_aux,
    o_i_ref,
    o_pc_ref,
    o_aux_ref,
    o_valid_ref,
    o_illegal_ref,
    o_wb_cyc_ref,
    o_wb_stb_ref,
    o_wb_we_ref,
    o_wb_addr_ref,
    o_wb_data_ref,
    i_wb_ack,
    i_wb_stall,
    i_wb_err,
    i_wb_data
);
parameter ADDRESS_WIDTH = 32;
parameter AUX_WIDTH = 1;
input i_clk;
input i_rst;
input i_ce;
input i_stalled_n;
input [31:0] i_pc;
input i_aux;
output reg [31:0] o_i_ref;
output reg [31:0] o_pc_ref;
output reg o_aux_ref;
output reg o_valid_ref;
output reg o_illegal_ref;
output reg o_wb_cyc_ref;
output reg o_wb_stb_ref;
output reg o_wb_we_ref;
output reg [31:0] o_wb_addr_ref;
output reg [31:0] o_wb_data_ref;
input i_wb_ack;
input i_wb_stall;
input i_wb_err;
input [31:0] i_wb_data;
longint unsigned o_i_ref__dpi;
longint unsigned o_pc_ref__dpi;
longint unsigned o_aux_ref__dpi;
longint unsigned o_valid_ref__dpi;
longint unsigned o_illegal_ref__dpi;
longint unsigned o_wb_cyc_ref__dpi;
longint unsigned o_wb_stb_ref__dpi;
longint unsigned o_wb_we_ref__dpi;
longint unsigned o_wb_addr_ref__dpi;
longint unsigned o_wb_data_ref__dpi;

always @(*) begin
    ref_model_eval(i_clk, i_rst, i_ce, i_stalled_n, i_pc, i_aux, o_i_ref__dpi, o_pc_ref__dpi, o_aux_ref__dpi, o_valid_ref__dpi, o_illegal_ref__dpi, o_wb_cyc_ref__dpi, o_wb_stb_ref__dpi, o_wb_we_ref__dpi, o_wb_addr_ref__dpi, o_wb_data_ref__dpi, i_wb_ack, i_wb_stall, i_wb_err, i_wb_data);
    o_i_ref = o_i_ref__dpi[31:0];
    o_pc_ref = o_pc_ref__dpi[31:0];
    o_aux_ref = o_aux_ref__dpi[0];
    o_valid_ref = o_valid_ref__dpi[0];
    o_illegal_ref = o_illegal_ref__dpi[0];
    o_wb_cyc_ref = o_wb_cyc_ref__dpi[0];
    o_wb_stb_ref = o_wb_stb_ref__dpi[0];
    o_wb_we_ref = o_wb_we_ref__dpi[0];
    o_wb_addr_ref = o_wb_addr_ref__dpi[31:0];
    o_wb_data_ref = o_wb_data_ref__dpi[31:0];
end
endmodule
