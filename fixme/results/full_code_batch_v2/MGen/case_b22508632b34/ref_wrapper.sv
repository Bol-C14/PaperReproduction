`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned in,
    input longint unsigned clk,
    input longint unsigned reset,
    output longint unsigned out__dpi
);

module mealy_nonol (
    in,
    clk,
    reset,
    out
);
input in;
input clk;
input reset;
output reg out;
longint unsigned out__dpi;

always @(*) begin
    ref_model_eval(in, clk, reset, out__dpi);
    out = out__dpi[0];
end
endmodule
