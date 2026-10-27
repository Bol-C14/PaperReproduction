module top(input [15:0] x, output [15:0] y0, output [15:0] y1, output [15:0] y2);
assign y0 = (((16'd1 * x) << 1) + x);
assign y1 = ((((x << 1) << 1) << 1) - x);
assign y2 = (((16'd10 * x) << 1) + x);
endmodule
