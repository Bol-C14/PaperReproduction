`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned i_a,
    input longint unsigned i_b,
    input longint unsigned i_cin,
    output longint unsigned o_sum__dpi,
    output longint unsigned o_carry__dpi
);

module full_half_add_1bit (
    i_a,
    i_b,
    i_cin,
    o_sum,
    o_carry
);
input i_a;
input i_b;
input i_cin;
output reg o_sum;
output reg o_carry;
longint unsigned o_sum__dpi;
longint unsigned o_carry__dpi;

always @(*) begin
    ref_model_eval(i_a, i_b, i_cin, o_sum__dpi, o_carry__dpi);
    o_sum = o_sum__dpi[0];
    o_carry = o_carry__dpi[0];
end
endmodule
