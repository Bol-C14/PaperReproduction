module top(input [15:0] x,output [15:0] y0,output [15:0] y1);
wire [15:0] n_fee510144b2f = (16'd5 * x);
wire [15:0] n_3595e26017eb = (16'd2 * x);
wire [15:0] n_772ecd5688d2 = (16'd11 * n_3595e26017eb);
wire [15:0] n_4254b18db5e4 = (n_772ecd5688d2 + x);
wire [15:0] n_aa6bef0dc814 = (n_4254b18db5e4 << 2);
wire [15:0] n_a257b22cb499 = (n_aa6bef0dc814 + x);
assign y0 = n_fee510144b2f;
assign y1 = n_a257b22cb499;
endmodule
