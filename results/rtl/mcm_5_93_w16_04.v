module top(input [15:0] x, output [15:0] y0, output [15:0] y1);
assign y0 = (x + (x << 2));
assign y1 = (((16'd46 * x) << 1) + x);
endmodule
