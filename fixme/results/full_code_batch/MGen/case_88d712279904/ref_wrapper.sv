`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned up_down,
    input longint unsigned clk,
    input longint unsigned reset,
    output longint unsigned bin_count__dpi
);

module cntr_3ud (
    up_down,
    clk,
    reset,
    bin_count
);
input up_down;
input clk;
input reset;
output reg [2:0] bin_count;
longint unsigned bin_count__dpi;

always @(*) begin
    ref_model_eval(up_down, clk, reset, bin_count__dpi);
    bin_count = bin_count__dpi[2:0];
end
endmodule
