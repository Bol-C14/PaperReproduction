module dut(input [15:0] x, output [15:0] y0, output [15:0] y1);
assign y0 = (x + (x << 2));
assign y1 = (((x + (x << 2)) + ((x << 3) + (x << 4))) + (x << 6));
endmodule
module miter(input [15:0] x, output bad);
wire [15:0] y0; wire [15:0] ref0 = x * 16'd5;
wire [15:0] y1; wire [15:0] ref1 = x * 16'd93;
dut d(.x(x),.y0(y0),.y1(y1));
assign bad = (|(y0 ^ ref0)) | (|(y1 ^ ref1));
endmodule
