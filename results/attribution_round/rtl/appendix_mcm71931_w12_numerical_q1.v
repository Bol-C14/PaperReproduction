module top(input [11:0] x,output [11:0] y0,output [11:0] y1,output [11:0] y2);
wire [11:0] n_9dd14cf16558 = (x << 3);
wire [11:0] n_489574fd2b1f = (n_9dd14cf16558 - x);
wire [11:0] n_b74bef5095f8 = (x << 4);
wire [11:0] n_c6bee8ea7d2b = (12'd3 * x);
wire [11:0] n_3e7eb6e01509 = (n_b74bef5095f8 + n_c6bee8ea7d2b);
wire [11:0] n_8e7f99efafc9 = (x << 5);
wire [11:0] n_0799512410af = (n_8e7f99efafc9 - x);
assign y0 = n_489574fd2b1f;
assign y1 = n_3e7eb6e01509;
assign y2 = n_0799512410af;
endmodule
