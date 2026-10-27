module top(input [15:0] x, output [15:0] y0, output [15:0] y1);
assign y0 = (16'd5 * x);
assign y1 = (16'd93 * x);
endmodule
