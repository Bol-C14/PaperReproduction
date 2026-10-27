`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned binary,
    output longint unsigned gray__dpi
);

module bin_gry (
    binary,
    gray
);
parameter N = 8



input       [N-1:0] binary;
input [7:0] binary;
output reg [7:0] gray;
longint unsigned gray__dpi;

always @(*) begin
    ref_model_eval(binary, gray__dpi);
    gray = gray__dpi[7:0];
end
endmodule
