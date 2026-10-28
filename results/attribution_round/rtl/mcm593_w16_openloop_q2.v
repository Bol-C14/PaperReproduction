module top(input [15:0] x,output [15:0] y0,output [15:0] y1);
wire [15:0] n_fee510144b2f = (16'd5 * x);
wire [15:0] n_3595e26017eb = (16'd2 * x);
wire [15:0] n_c03c4695ad19 = (16'd23 * n_3595e26017eb);
wire [15:0] n_2852bf461290 = (n_c03c4695ad19 << 1);
wire [15:0] n_a257b22cb499 = (n_2852bf461290 + x);
assign y0 = n_fee510144b2f;
assign y1 = n_a257b22cb499;
endmodule
