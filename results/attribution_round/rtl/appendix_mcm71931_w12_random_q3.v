module top(input [11:0] x,output [11:0] y0,output [11:0] y1,output [11:0] y2);
wire [11:0] n_fee510144b2f = (12'd7 * x);
wire [11:0] n_372383f442af = (12'd19 * x);
wire [11:0] n_aa6bef0dc814 = (n_fee510144b2f << 1);
wire [11:0] n_4254b18db5e4 = (n_aa6bef0dc814 + x);
wire [11:0] n_cca52b76c874 = (n_4254b18db5e4 << 1);
wire [11:0] n_cc57092683ea = (n_cca52b76c874 + x);
assign y0 = n_fee510144b2f;
assign y1 = n_372383f442af;
assign y2 = n_cc57092683ea;
endmodule
