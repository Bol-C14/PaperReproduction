module top(input [11:0] x,output [11:0] y0,output [11:0] y1,output [11:0] y2);
wire [11:0] n_9dd14cf16558 = (x << 3);
wire [11:0] n_489574fd2b1f = (n_9dd14cf16558 - x);
wire [11:0] n_9d73ec35baa7 = (12'd9 * x);
wire [11:0] n_2852bf461290 = (n_9d73ec35baa7 << 1);
wire [11:0] n_a257b22cb499 = (n_2852bf461290 + x);
wire [11:0] n_8e7f99efafc9 = (x << 5);
wire [11:0] n_0799512410af = (n_8e7f99efafc9 - x);
assign y0 = n_489574fd2b1f;
assign y1 = n_a257b22cb499;
assign y2 = n_0799512410af;
endmodule
