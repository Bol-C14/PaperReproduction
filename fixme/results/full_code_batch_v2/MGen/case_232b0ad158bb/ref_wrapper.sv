`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned data_in,
    input longint unsigned load,
    input longint unsigned shift_en,
    input longint unsigned clk,
    input longint unsigned reset,
    output longint unsigned data_out__dpi
);

module pipo_shift (
    data_in,
    load,
    shift_en,
    clk,
    reset,
    data_out
);
input [15:0] data_in;
input load;
input [1:0] shift_en;
input clk;
input reset;
output reg [15:0] data_out;
longint unsigned data_out__dpi;

always @(*) begin
    ref_model_eval(data_in, load, shift_en, clk, reset, data_out__dpi);
    data_out = data_out__dpi[15:0];
end
endmodule
