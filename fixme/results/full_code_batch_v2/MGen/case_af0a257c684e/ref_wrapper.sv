`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clock,
    input longint unsigned clk_en,
    input longint unsigned aclr,
    input longint unsigned dataa,
    input longint unsigned datab,
    output longint unsigned ref_result__dpi,
    output longint unsigned ref_overflow__dpi,
    output longint unsigned ref_underflow__dpi,
    output longint unsigned ref_zero__dpi,
    output longint unsigned ref_denormal__dpi,
    output longint unsigned ref_indefinite__dpi,
    output longint unsigned ref_nan__dpi
);

module ref_altfp_mult (
    clock,
    clk_en,
    aclr,
    dataa,
    datab,
    ref_result,
    ref_overflow,
    ref_underflow,
    ref_zero,
    ref_denormal,
    ref_indefinite,
    ref_nan
);
input clock;
input clk_en;
input aclr;
input [31:0] dataa;
input [31:0] datab;
output reg [31:0] ref_result;
output reg ref_overflow;
output reg ref_underflow;
output reg ref_zero;
output reg ref_denormal;
output reg ref_indefinite;
output reg ref_nan;
longint unsigned ref_result__dpi;
longint unsigned ref_overflow__dpi;
longint unsigned ref_underflow__dpi;
longint unsigned ref_zero__dpi;
longint unsigned ref_denormal__dpi;
longint unsigned ref_indefinite__dpi;
longint unsigned ref_nan__dpi;

always @(*) begin
    ref_model_eval(clock, clk_en, aclr, dataa, datab, ref_result__dpi, ref_overflow__dpi, ref_underflow__dpi, ref_zero__dpi, ref_denormal__dpi, ref_indefinite__dpi, ref_nan__dpi);
    ref_result = ref_result__dpi[31:0];
    ref_overflow = ref_overflow__dpi[0];
    ref_underflow = ref_underflow__dpi[0];
    ref_zero = ref_zero__dpi[0];
    ref_denormal = ref_denormal__dpi[0];
    ref_indefinite = ref_indefinite__dpi[0];
    ref_nan = ref_nan__dpi[0];
end
endmodule
