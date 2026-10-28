module dut(input [11:0] x,output [11:0] y0,output [11:0] y1,output [11:0] y2);
wire [11:0] n_fee510144b2f = (12'd7 * x);
wire [11:0] n_372383f442af = (12'd19 * x);
wire [11:0] n_3595e26017eb = (12'd31 * x);
assign y0 = n_fee510144b2f;
assign y1 = n_372383f442af;
assign y2 = n_3595e26017eb;
endmodule
module miter(input [11:0] x,output bad);
wire [11:0] y0; wire [11:0] r0 = (12'd7 * x);
wire [11:0] y1; wire [11:0] r1 = (12'd19 * x);
wire [11:0] y2; wire [11:0] r2 = (12'd31 * x);
dut d(.x(x),.y0(y0),.y1(y1),.y2(y2));
assign bad = (|(y0 ^ r0)) | (|(y1 ^ r1)) | (|(y2 ^ r2));
endmodule
