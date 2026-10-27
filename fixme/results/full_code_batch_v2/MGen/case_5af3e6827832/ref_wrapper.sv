`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned i_clk,
    input longint unsigned i_wreq,
    input longint unsigned i_ereq,
    input longint unsigned i_pipewr,
    input longint unsigned i_endpipe,
    input longint unsigned i_addr,
    input longint unsigned i_data,
    output longint unsigned ref_o_bus_ack__dpi,
    output longint unsigned ref_o_qspi_req__dpi,
    input longint unsigned i_qspi_grant,
    output longint unsigned ref_o_spi_wr__dpi,
    output longint unsigned ref_o_spi_hold__dpi,
    output longint unsigned ref_o_spi_word__dpi,
    output longint unsigned ref_o_spi_len__dpi,
    output longint unsigned ref_o_spi_spd__dpi,
    output longint unsigned ref_o_spi_dir__dpi,
    input longint unsigned i_spi_data,
    input longint unsigned i_spi_valid,
    input longint unsigned i_spi_busy,
    input longint unsigned i_spi_stopped,
    output longint unsigned ref_o_data_ack__dpi,
    input longint unsigned i_quad,
    output longint unsigned ref_o_wip__dpi
);

module ref_writeqspi (
    i_clk,
    i_wreq,
    i_ereq,
    i_pipewr,
    i_endpipe,
    i_addr,
    i_data,
    ref_o_bus_ack,
    ref_o_qspi_req,
    i_qspi_grant,
    ref_o_spi_wr,
    ref_o_spi_hold,
    ref_o_spi_word,
    ref_o_spi_len,
    ref_o_spi_spd,
    ref_o_spi_dir,
    i_spi_data,
    i_spi_valid,
    i_spi_busy,
    i_spi_stopped,
    ref_o_data_ack,
    i_quad,
    ref_o_wip
);
input i_clk;
input i_wreq;
input i_ereq;
input i_pipewr;
input i_endpipe;
input [21:0] i_addr;
input [31:0] i_data;
output reg ref_o_bus_ack;
output reg ref_o_qspi_req;
input i_qspi_grant;
output reg ref_o_spi_wr;
output reg ref_o_spi_hold;
output reg [31:0] ref_o_spi_word;
output reg [1:0] ref_o_spi_len;
output reg ref_o_spi_spd;
output reg ref_o_spi_dir;
input [31:0] i_spi_data;
input i_spi_valid;
input i_spi_busy;
input i_spi_stopped;
output reg ref_o_data_ack;
input i_quad;
output reg ref_o_wip;
longint unsigned ref_o_bus_ack__dpi;
longint unsigned ref_o_qspi_req__dpi;
longint unsigned ref_o_spi_wr__dpi;
longint unsigned ref_o_spi_hold__dpi;
longint unsigned ref_o_spi_word__dpi;
longint unsigned ref_o_spi_len__dpi;
longint unsigned ref_o_spi_spd__dpi;
longint unsigned ref_o_spi_dir__dpi;
longint unsigned ref_o_data_ack__dpi;
longint unsigned ref_o_wip__dpi;

always @(*) begin
    ref_model_eval(i_clk, i_wreq, i_ereq, i_pipewr, i_endpipe, i_addr, i_data, ref_o_bus_ack__dpi, ref_o_qspi_req__dpi, i_qspi_grant, ref_o_spi_wr__dpi, ref_o_spi_hold__dpi, ref_o_spi_word__dpi, ref_o_spi_len__dpi, ref_o_spi_spd__dpi, ref_o_spi_dir__dpi, i_spi_data, i_spi_valid, i_spi_busy, i_spi_stopped, ref_o_data_ack__dpi, i_quad, ref_o_wip__dpi);
    ref_o_bus_ack = ref_o_bus_ack__dpi[0];
    ref_o_qspi_req = ref_o_qspi_req__dpi[0];
    ref_o_spi_wr = ref_o_spi_wr__dpi[0];
    ref_o_spi_hold = ref_o_spi_hold__dpi[0];
    ref_o_spi_word = ref_o_spi_word__dpi[31:0];
    ref_o_spi_len = ref_o_spi_len__dpi[1:0];
    ref_o_spi_spd = ref_o_spi_spd__dpi[0];
    ref_o_spi_dir = ref_o_spi_dir__dpi[0];
    ref_o_data_ack = ref_o_data_ack__dpi[0];
    ref_o_wip = ref_o_wip__dpi[0];
end
endmodule
