module top(input [7:0] x, output [7:0] y0, output [7:0] y1);
assign y0 = (x + (x << 2));
assign y1 = ((((((((((x << 1) << 1) - x) << 1) << 1) << 1) - x) << 1) << 1) + x);
endmodule
