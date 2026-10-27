module top(input [7:0] x0,input [7:0] x1,input [7:0] x2,output [7:0] y0);
assign y0 = (((8'd20 * x1) << 1) + ((8'd12 * x0) + (x1 + (8'd21 * x2))));
endmodule
