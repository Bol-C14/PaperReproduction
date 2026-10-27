module top(input [7:0] x, output [7:0] y0, output [7:0] y1, output [7:0] y2);
assign y0 = (x + (x << 1));
assign y1 = (8'd7 * x);
assign y2 = (((8'd10 * x) << 1) + x);
endmodule
