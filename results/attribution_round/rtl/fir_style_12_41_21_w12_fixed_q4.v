module top(input [11:0] x0,input [11:0] x1,input [11:0] x2,output [11:0] y0);
wire [11:0] n_fee510144b2f = (12'd12 * x0);
wire [11:0] n_c6bee8ea7d2b = (12'd20 * x1);
wire [11:0] n_e51b07517ec7 = (n_c6bee8ea7d2b << 1);
wire [11:0] n_cc57092683ea = (n_e51b07517ec7 + x1);
wire [11:0] n_7faebb8dce38 = (n_fee510144b2f + n_cc57092683ea);
wire [11:0] n_3595e26017eb = (12'd21 * x2);
wire [11:0] n_a257b22cb499 = (n_7faebb8dce38 + n_3595e26017eb);
assign y0 = n_a257b22cb499;
endmodule
