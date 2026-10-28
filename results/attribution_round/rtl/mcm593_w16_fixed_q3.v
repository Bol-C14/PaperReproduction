module top(input [15:0] x,output [15:0] y0,output [15:0] y1);
wire [15:0] n_3595e26017eb = (16'd2 * x);
wire [15:0] n_e51b07517ec7 = (n_3595e26017eb << 1);
wire [15:0] n_7faebb8dce38 = (n_e51b07517ec7 + x);
wire [15:0] n_372383f442af = (16'd93 * x);
assign y0 = n_7faebb8dce38;
assign y1 = n_372383f442af;
endmodule
