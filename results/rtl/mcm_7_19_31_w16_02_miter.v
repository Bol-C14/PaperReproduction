module dut(input [15:0] x, output [15:0] y0, output [15:0] y1, output [15:0] y2);
assign y0 = ((((x << 1) << 1) << 1) - x);
assign y1 = ((((((x << 1) << 1) + x) << 1) << 1) - x);
assign y2 = ((((((x << 1) << 1) << 1) << 1) << 1) - x);
endmodule
module miter(input [15:0] x, output bad);
wire [15:0] y0; wire [15:0] ref0 = x * 16'd7;
wire [15:0] y1; wire [15:0] ref1 = x * 16'd19;
wire [15:0] y2; wire [15:0] ref2 = x * 16'd31;
dut d(.x(x),.y0(y0),.y1(y1),.y2(y2));
assign bad = (|(y0 ^ ref0)) | (|(y1 ^ ref1)) | (|(y2 ^ ref2));
endmodule
