`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned reset,
    input longint unsigned data_i,
    output longint unsigned data_o_ref__dpi
);

module fht_ref (
    clk,
    reset,
    data_i,
    data_o_ref
);
input clk;
input reset;
input [7:0] data_i;
output reg [7:0] data_o_ref;
longint unsigned data_o_ref__dpi;

always @(*) begin
    ref_model_eval(clk, reset, data_i, data_o_ref__dpi);
    data_o_ref = data_o_ref__dpi[7:0];
end
endmodule
