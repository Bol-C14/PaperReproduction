module top(input [15:0] x, output [15:0] y0, output [15:0] y1);
assign y0 = (((x << 1) << 1) + x);
assign y1 = (((x + (x << 2)) + ((x << 3) + (x << 4))) + (x << 6));
endmodule
