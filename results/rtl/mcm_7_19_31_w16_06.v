module top(input [15:0] x, output [15:0] y0, output [15:0] y1, output [15:0] y2);
assign y0 = (16'd7 * x);
assign y1 = ((x + (x << 1)) + (x << 4));
assign y2 = (((16'd15 * x) << 1) + x);
endmodule
