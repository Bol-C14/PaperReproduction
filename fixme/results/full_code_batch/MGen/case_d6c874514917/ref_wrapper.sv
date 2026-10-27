`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned rst_i,
    input longint unsigned clk_i,
    input longint unsigned stb_i,
    input longint unsigned we_i,
    output longint unsigned ref_dat_o__dpi,
    input longint unsigned dat_i,
    output longint unsigned ref_int_o__dpi,
    input longint unsigned adr_i,
    output longint unsigned ref_MOSI__dpi,
    output longint unsigned ref_SCLK__dpi,
    input longint unsigned MISO
);

module ref_tiny_spi (
    rst_i,
    clk_i,
    stb_i,
    we_i,
    ref_dat_o,
    dat_i,
    ref_int_o,
    adr_i,
    ref_MOSI,
    ref_SCLK,
    MISO
);
parameter BAUD_WIDTH = 8;
parameter BAUD_DIV = 0;
parameter SPI_MODE = 0;
parameter BC_WIDTH = 3;
parameter DIV_WIDTH = BAUD_DIV ? $clog2(BAUD_DIV / 2 - 1) : BAUD_WIDTH;
parameter IDLE = 0;
parameter PHASE1 = 1;
parameter PHASE2 = 2;
input rst_i;
input clk_i;
input stb_i;
input we_i;
output reg [31:0] ref_dat_o;
input [31:0] dat_i;
output reg ref_int_o;
input [2:0] adr_i;
output reg ref_MOSI;
output reg ref_SCLK;
input MISO;
longint unsigned ref_dat_o__dpi;
longint unsigned ref_int_o__dpi;
longint unsigned ref_MOSI__dpi;
longint unsigned ref_SCLK__dpi;

always @(*) begin
    ref_model_eval(rst_i, clk_i, stb_i, we_i, ref_dat_o__dpi, dat_i, ref_int_o__dpi, adr_i, ref_MOSI__dpi, ref_SCLK__dpi, MISO);
    ref_dat_o = ref_dat_o__dpi[31:0];
    ref_int_o = ref_int_o__dpi[0];
    ref_MOSI = ref_MOSI__dpi[0];
    ref_SCLK = ref_SCLK__dpi[0];
end
endmodule
