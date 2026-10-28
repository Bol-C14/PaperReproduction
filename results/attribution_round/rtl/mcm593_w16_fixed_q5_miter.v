module dut(input [15:0] x,output [15:0] y0,output [15:0] y1);
wire [15:0] n_8e7f99efafc9 = (x << 2);
wire [15:0] n_7faebb8dce38 = (n_8e7f99efafc9 + x);
wire [15:0] n_c6bee8ea7d2b = (16'd46 * x);
wire [15:0] n_2852bf461290 = (n_c6bee8ea7d2b << 1);
wire [15:0] n_a257b22cb499 = (n_2852bf461290 + x);
assign y0 = n_7faebb8dce38;
assign y1 = n_a257b22cb499;
endmodule
module miter(input [15:0] x,output bad);
wire [15:0] y0; wire [15:0] r0 = (16'd5 * x);
wire [15:0] y1; wire [15:0] r1 = (16'd93 * x);
dut d(.x(x),.y0(y0),.y1(y1));
assign bad = (|(y0 ^ r0)) | (|(y1 ^ r1));
endmodule
