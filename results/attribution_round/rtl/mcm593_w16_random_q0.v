module top(input [15:0] x,output [15:0] y0,output [15:0] y1);
wire [15:0] n_fee510144b2f = (16'd5 * x);
wire [15:0] n_372383f442af = (16'd93 * x);
assign y0 = n_fee510144b2f;
assign y1 = n_372383f442af;
endmodule
