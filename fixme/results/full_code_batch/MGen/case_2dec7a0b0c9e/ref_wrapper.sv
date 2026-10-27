`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned a,
    input longint unsigned b,
    input longint unsigned select,
    output longint unsigned zero__dpi,
    output longint unsigned carry__dpi,
    output longint unsigned sign__dpi,
    output longint unsigned parity__dpi,
    output longint unsigned overflow__dpi,
    output longint unsigned out__dpi
);

module alu (
    a,
    b,
    select,
    zero,
    carry,
    sign,
    parity,
    overflow,
    out
);
input [3:0] a;
input [3:0] b;
input [1:0] select;
output reg zero;
output reg carry;
output reg sign;
output reg parity;
output reg overflow;
output reg [3:0] out;
longint unsigned zero__dpi;
longint unsigned carry__dpi;
longint unsigned sign__dpi;
longint unsigned parity__dpi;
longint unsigned overflow__dpi;
longint unsigned out__dpi;

always @(*) begin
    ref_model_eval(a, b, select, zero__dpi, carry__dpi, sign__dpi, parity__dpi, overflow__dpi, out__dpi);
    zero = zero__dpi[0];
    carry = carry__dpi[0];
    sign = sign__dpi[0];
    parity = parity__dpi[0];
    overflow = overflow__dpi[0];
    out = out__dpi[3:0];
end
endmodule
