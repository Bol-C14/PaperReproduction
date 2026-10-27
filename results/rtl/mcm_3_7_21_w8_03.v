module top(input [7:0] x, output [7:0] y0, output [7:0] y1, output [7:0] y2);
assign y0 = (((8'd1 * x) << 1) + x);
assign y1 = (((8'd3 * x) << 1) + x);
assign y2 = (((8'd10 * x) << 1) + x);
endmodule
