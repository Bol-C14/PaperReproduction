`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned reset,
    input longint unsigned clk,
    output longint unsigned data_out__dpi
);

module lfsr (
    reset,
    clk,
    data_out
);
input reset;
input clk;
output reg [3:0] data_out;
longint unsigned data_out__dpi;

always @(*) begin
    ref_model_eval(reset, clk, data_out__dpi);
    data_out = data_out__dpi[3:0];
end
endmodule
