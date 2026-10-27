`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned rst,
    input longint unsigned enable,
    input longint unsigned rmode,
    input longint unsigned opa,
    input longint unsigned opb,
    input longint unsigned in_except,
    input longint unsigned exponent_in,
    input longint unsigned mantissa_in,
    input longint unsigned fpu_op,
    output longint unsigned ref_out__dpi,
    output longint unsigned ref_ex_enable__dpi,
    output longint unsigned ref_underflow__dpi,
    output longint unsigned ref_overflow__dpi,
    output longint unsigned ref_inexact__dpi,
    output longint unsigned ref_exception__dpi,
    output longint unsigned ref_invalid__dpi
);

module ref_fpu_exceptions (
    clk,
    rst,
    enable,
    rmode,
    opa,
    opb,
    in_except,
    exponent_in,
    mantissa_in,
    fpu_op,
    ref_out,
    ref_ex_enable,
    ref_underflow,
    ref_overflow,
    ref_inexact,
    ref_exception,
    ref_invalid
);
input clk;
input rst;
input enable;
input [1:0] rmode;
input [63:0] opa;
input [63:0] opb;
input [63:0] in_except;
input [11:0] exponent_in;
input [1:0] mantissa_in;
input [2:0] fpu_op;
output reg [63:0] ref_out;
output reg ref_ex_enable;
output reg ref_underflow;
output reg ref_overflow;
output reg ref_inexact;
output reg ref_exception;
output reg ref_invalid;
longint unsigned ref_out__dpi;
longint unsigned ref_ex_enable__dpi;
longint unsigned ref_underflow__dpi;
longint unsigned ref_overflow__dpi;
longint unsigned ref_inexact__dpi;
longint unsigned ref_exception__dpi;
longint unsigned ref_invalid__dpi;

always @(*) begin
    ref_model_eval(clk, rst, enable, rmode, opa, opb, in_except, exponent_in, mantissa_in, fpu_op, ref_out__dpi, ref_ex_enable__dpi, ref_underflow__dpi, ref_overflow__dpi, ref_inexact__dpi, ref_exception__dpi, ref_invalid__dpi);
    ref_out = ref_out__dpi[63:0];
    ref_ex_enable = ref_ex_enable__dpi[0];
    ref_underflow = ref_underflow__dpi[0];
    ref_overflow = ref_overflow__dpi[0];
    ref_inexact = ref_inexact__dpi[0];
    ref_exception = ref_exception__dpi[0];
    ref_invalid = ref_invalid__dpi[0];
end
endmodule
