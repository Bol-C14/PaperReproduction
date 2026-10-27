module dut(input [7:0] x, output [7:0] y0, output [7:0] y1);
assign y0 = (x + (x << 2));
assign y1 = (((x + (x << 2)) + ((x << 3) + (x << 4))) + (x << 6));
endmodule
module miter(input [7:0] x, output bad);
wire [7:0] y0; wire [7:0] ref0 = x * 8'd5;
wire [7:0] y1; wire [7:0] ref1 = x * 8'd93;
dut d(.x(x),.y0(y0),.y1(y1));
assign bad = (|(y0 ^ ref0)) | (|(y1 ^ ref1));
endmodule
