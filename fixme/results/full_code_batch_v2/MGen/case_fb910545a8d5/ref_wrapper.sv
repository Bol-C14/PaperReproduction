`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk_i,
    input longint unsigned rst_i,
    input longint unsigned draw_line_i,
    input longint unsigned read_pixel_i,
    output longint unsigned ref_busy_o__dpi,
    output longint unsigned ref_x_major_o__dpi,
    output longint unsigned ref_valid_o__dpi
);

module ref_bresenham_line (
    clk_i,
    rst_i,
    draw_line_i,
    read_pixel_i,
    ref_busy_o,
    ref_x_major_o,
    ref_valid_o
);
input clk_i;
input rst_i;
input draw_line_i;
input read_pixel_i;
output reg ref_busy_o;
output reg ref_x_major_o;
output reg ref_valid_o;
longint unsigned ref_busy_o__dpi;
longint unsigned ref_x_major_o__dpi;
longint unsigned ref_valid_o__dpi;

always @(*) begin
    ref_model_eval(clk_i, rst_i, draw_line_i, read_pixel_i, ref_busy_o__dpi, ref_x_major_o__dpi, ref_valid_o__dpi);
    ref_busy_o = ref_busy_o__dpi[0];
    ref_x_major_o = ref_x_major_o__dpi[0];
    ref_valid_o = ref_valid_o__dpi[0];
end
endmodule
