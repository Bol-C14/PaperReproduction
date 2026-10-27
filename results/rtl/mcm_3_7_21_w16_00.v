module top(input [15:0] x, output [15:0] y0, output [15:0] y1, output [15:0] y2);
assign y0 = (16'd3 * x);
assign y1 = (16'd7 * x);
assign y2 = (16'd21 * x);
endmodule
