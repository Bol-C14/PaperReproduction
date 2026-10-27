`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned x,
    input longint unsigned clk,
    input longint unsigned reset,
    output longint unsigned y__dpi
);

module custdesign (
    x,
    clk,
    reset,
    y
);
input x;
input clk;
input reset;
output reg y;
longint unsigned y__dpi;

always @(*) begin
    ref_model_eval(x, clk, reset, y__dpi);
    y = y__dpi[0];
end
endmodule
