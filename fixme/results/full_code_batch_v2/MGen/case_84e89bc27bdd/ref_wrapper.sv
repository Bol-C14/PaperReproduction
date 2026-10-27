`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned in0,
    input longint unsigned in1,
    input longint unsigned select,
    output longint unsigned out__dpi
);

module mux_always (
    in0,
    in1,
    select,
    out
);
input in0;
input in1;
input select;
output reg out;
longint unsigned out__dpi;

always @(*) begin
    ref_model_eval(in0, in1, select, out__dpi);
    out = out__dpi[0];
end
endmodule
