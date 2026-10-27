`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned data1_i,
    input longint unsigned data2_i,
    input longint unsigned select_i
);

module MUX32_ref (
    data1_i,
    data2_i,
    select_i
);
input [31:0] data1_i;
input [31:0] data2_i;
input select_i;

always @(*) begin
    ref_model_eval(data1_i, data2_i, select_i);
end
endmodule
