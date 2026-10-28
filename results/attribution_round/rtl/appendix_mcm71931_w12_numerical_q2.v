module top(input [11:0] x,output [11:0] y0,output [11:0] y1,output [11:0] y2);
wire [11:0] n_c6bee8ea7d2b = (12'd3 * x);
wire [11:0] n_e51b07517ec7 = (n_c6bee8ea7d2b << 1);
wire [11:0] n_7faebb8dce38 = (n_e51b07517ec7 + x);
wire [11:0] n_9d73ec35baa7 = (12'd9 * x);
wire [11:0] n_2852bf461290 = (n_9d73ec35baa7 << 1);
wire [11:0] n_a257b22cb499 = (n_2852bf461290 + x);
wire [11:0] n_c03c4695ad19 = (12'd15 * x);
wire [11:0] n_cca52b76c874 = (n_c03c4695ad19 << 1);
wire [11:0] n_cc57092683ea = (n_cca52b76c874 + x);
assign y0 = n_7faebb8dce38;
assign y1 = n_a257b22cb499;
assign y2 = n_cc57092683ea;
endmodule
