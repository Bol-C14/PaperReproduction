`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned data_in,
    input longint unsigned control,
    input longint unsigned clk,
    input longint unsigned reset,
    output longint unsigned data_out__dpi
);

module univ_shift (
    data_in,
    control,
    clk,
    reset,
    data_out
);
parameter n = 4;
input [3:0] data_in;
input [1:0] control;
input clk;
input reset;
output reg [3:0] data_out;
longint unsigned data_out__dpi;

always @(*) begin
    ref_model_eval(data_in, control, clk, reset, data_out__dpi);
    data_out = data_out__dpi[3:0];
end
endmodule
