`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    output longint unsigned e_ref__dpi,
    input longint unsigned q
);

module sparc_exu_ecc_dec_ref (
    e_ref,
    q
);
output reg [63:0] e_ref;
input [6:0] q;
longint unsigned e_ref__dpi;

always @(*) begin
    ref_model_eval(e_ref__dpi, q);
    e_ref = e_ref__dpi[63:0];
end
endmodule
