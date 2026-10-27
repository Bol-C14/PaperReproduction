module top(input [15:0] x, output [15:0] y0, output [15:0] y1, output [15:0] y2);
assign y0 = (x + (x << 1));
assign y1 = ((x + (x << 1)) + (x << 2));
assign y2 = ((x + (x << 2)) + (x << 4));
endmodule
