`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned reset,
    input longint unsigned write_en,
    input longint unsigned read_en,
    input longint unsigned data_in,
    output longint unsigned full__dpi,
    output longint unsigned empty__dpi,
    output longint unsigned out__dpi
);

module top (
    clk,
    reset,
    write_en,
    read_en,
    data_in,
    full,
    empty,
    out
);
input clk;
input reset;
input write_en;
input read_en;
input [7:0] data_in;
output reg full;
output reg empty;
output reg [7:0] out;
longint unsigned full__dpi;
longint unsigned empty__dpi;
longint unsigned out__dpi;

always @(*) begin
    ref_model_eval(clk, reset, write_en, read_en, data_in, full__dpi, empty__dpi, out__dpi);
    full = full__dpi[0];
    empty = empty__dpi[0];
    out = out__dpi[7:0];
end
endmodule
