module top(input [7:0] x, output [7:0] y0, output [7:0] y1);
assign y0 = (8'd5 * x);
assign y1 = (8'd93 * x);
endmodule
