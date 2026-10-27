`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned i_a,
    input longint unsigned clk,
    input longint unsigned reset,
    output longint unsigned no_ones__dpi
);

module no_1s (
    i_a,
    clk,
    reset,
    no_ones
);
input [15:0] i_a;
input clk;
input reset;
output reg [3:0] no_ones;
longint unsigned no_ones__dpi;

always @(*) begin
    ref_model_eval(i_a, clk, reset, no_ones__dpi);
    no_ones = no_ones__dpi[3:0];
end
endmodule
