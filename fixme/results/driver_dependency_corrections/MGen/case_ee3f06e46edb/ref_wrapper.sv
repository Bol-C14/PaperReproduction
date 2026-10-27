`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned rst,
    input longint unsigned enable,
    input longint unsigned opa,
    input longint unsigned opb,
    output longint unsigned ref_sign__dpi,
    output longint unsigned ref_mantissa_7__dpi,
    output longint unsigned ref_exponent_out__dpi
);

module ref_fpu_div (
    clk,
    rst,
    enable,
    opa,
    opb,
    ref_sign,
    ref_mantissa_7,
    ref_exponent_out
);
input clk;
input rst;
input enable;
input [63:0] opa;
input [63:0] opb;
output reg ref_sign;
output reg [55:0] ref_mantissa_7;
output reg [11:0] ref_exponent_out;
longint unsigned ref_sign__dpi;
longint unsigned ref_mantissa_7__dpi;
longint unsigned ref_exponent_out__dpi;

always @(*) begin
    ref_model_eval(clk, rst, enable, opa, opb, ref_sign__dpi, ref_mantissa_7__dpi, ref_exponent_out__dpi);
    ref_sign = ref_sign__dpi[0];
    ref_mantissa_7 = ref_mantissa_7__dpi[55:0];
    ref_exponent_out = ref_exponent_out__dpi[11:0];
end
endmodule
