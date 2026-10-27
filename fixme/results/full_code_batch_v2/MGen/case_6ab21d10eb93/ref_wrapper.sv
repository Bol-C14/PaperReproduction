`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned in0,
    input longint unsigned in1,
    input longint unsigned in2,
    input longint unsigned in3,
    input longint unsigned select,
    output longint unsigned out__dpi
);

module mux_condt (
    in0,
    in1,
    in2,
    in3,
    select,
    out
);
input [1:0] in0;
input [1:0] in1;
input [1:0] in2;
input [1:0] in3;
input [1:0] select;
output reg [1:0] out;
longint unsigned out__dpi;

always @(*) begin
    ref_model_eval(in0, in1, in2, in3, select, out__dpi);
    out = out__dpi[1:0];
end
endmodule
