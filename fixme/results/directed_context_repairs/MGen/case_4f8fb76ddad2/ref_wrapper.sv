`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned i_clk,
    input longint unsigned i_rst,
    input longint unsigned i_wr,
    input longint unsigned i_signed,
    input longint unsigned i_numerator,
    input longint unsigned i_denominator,
    output longint unsigned o_busy_ref__dpi,
    output longint unsigned o_valid_ref__dpi,
    output longint unsigned o_err_ref__dpi,
    output longint unsigned o_quotient_ref__dpi,
    output longint unsigned o_flags_ref__dpi
);

module div_ref (
    i_clk,
    i_rst,
    i_wr,
    i_signed,
    i_numerator,
    i_denominator,
    o_busy_ref,
    o_valid_ref,
    o_err_ref,
    o_quotient_ref,
    o_flags_ref
);
parameter BW = 32;
input i_clk;
input i_rst;
input i_wr;
input i_signed;
input [31:0] i_numerator;
input [31:0] i_denominator;
output reg o_busy_ref;
output reg o_valid_ref;
output reg o_err_ref;
output reg [31:0] o_quotient_ref;
output reg [3:0] o_flags_ref;
longint unsigned o_busy_ref__dpi;
longint unsigned o_valid_ref__dpi;
longint unsigned o_err_ref__dpi;
longint unsigned o_quotient_ref__dpi;
longint unsigned o_flags_ref__dpi;

always @(*) begin
    ref_model_eval(i_clk, i_rst, i_wr, i_signed, i_numerator, i_denominator, o_busy_ref__dpi, o_valid_ref__dpi, o_err_ref__dpi, o_quotient_ref__dpi, o_flags_ref__dpi);
    o_busy_ref = o_busy_ref__dpi[0];
    o_valid_ref = o_valid_ref__dpi[0];
    o_err_ref = o_err_ref__dpi[0];
    o_quotient_ref = o_quotient_ref__dpi[31:0];
    o_flags_ref = o_flags_ref__dpi[3:0];
end
endmodule
