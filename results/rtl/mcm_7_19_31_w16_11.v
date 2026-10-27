module top(input [15:0] x, output [15:0] y0, output [15:0] y1, output [15:0] y2);
assign y0 = (((16'd3 * x) << 1) + x);
assign y1 = ((((((x << 1) << 1) + x) << 1) << 1) - x);
assign y2 = (((16'd15 * x) << 1) + x);
endmodule
