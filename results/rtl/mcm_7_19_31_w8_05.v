module top(input [7:0] x, output [7:0] y0, output [7:0] y1, output [7:0] y2);
assign y0 = ((x + (x << 1)) + (x << 2));
assign y1 = ((((((x << 1) << 1) + x) << 1) << 1) - x);
assign y2 = (((x + (x << 1)) + ((x << 2) + (x << 3))) + (x << 4));
endmodule
