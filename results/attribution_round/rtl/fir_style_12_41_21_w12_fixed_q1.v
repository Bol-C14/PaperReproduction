module top(input [11:0] x0,input [11:0] x1,input [11:0] x2,output [11:0] y0);
wire [11:0] n_c03c4695ad19 = (12'd2 * x0);
wire [11:0] n_772ecd5688d2 = (12'd6 * n_c03c4695ad19);
wire [11:0] n_372383f442af = (12'd41 * x1);
wire [11:0] n_7faebb8dce38 = (n_772ecd5688d2 + n_372383f442af);
wire [11:0] n_3595e26017eb = (12'd21 * x2);
wire [11:0] n_a257b22cb499 = (n_7faebb8dce38 + n_3595e26017eb);
assign y0 = n_a257b22cb499;
endmodule
