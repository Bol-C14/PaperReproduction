module top(input [7:0] x, output [7:0] y0, output [7:0] y1, output [7:0] y2);
assign y0 = (8'd7 * x);
assign y1 = ((x + (x << 1)) + (x << 4));
assign y2 = (((8'd15 * x) << 1) + x);
endmodule
