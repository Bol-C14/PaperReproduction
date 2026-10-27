`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned reset,
    input longint unsigned clk,
    output longint unsigned out_clk__dpi
);

module clkdivider (
    reset,
    clk,
    out_clk
);
input reset;
input clk;
output reg out_clk;
longint unsigned out_clk__dpi;

always @(*) begin
    ref_model_eval(reset, clk, out_clk__dpi);
    out_clk = out_clk__dpi[0];
end
endmodule
