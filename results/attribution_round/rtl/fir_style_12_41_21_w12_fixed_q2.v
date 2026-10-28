module top(input [11:0] x0,input [11:0] x1,input [11:0] x2,output [11:0] y0);
wire [11:0] n_9dd14cf16558 = (x0 << 2);
wire [11:0] n_a36f3993cd15 = (12'd3 * n_9dd14cf16558);
wire [11:0] n_372383f442af = (12'd41 * x1);
wire [11:0] n_7faebb8dce38 = (n_a36f3993cd15 + n_372383f442af);
wire [11:0] n_3595e26017eb = (12'd21 * x2);
wire [11:0] n_a257b22cb499 = (n_7faebb8dce38 + n_3595e26017eb);
assign y0 = n_a257b22cb499;
endmodule
