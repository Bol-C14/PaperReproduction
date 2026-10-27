module top(input [7:0] x,output [7:0] y0);
assign y0 = (((8'd5 * x) << 1) + x);
endmodule
