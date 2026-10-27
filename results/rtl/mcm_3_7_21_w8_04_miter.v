module dut(input [7:0] x, output [7:0] y0, output [7:0] y1, output [7:0] y2);
assign y0 = (x + (x << 1));
assign y1 = ((x + (x << 1)) + (x << 2));
assign y2 = (((8'd10 * x) << 1) + x);
endmodule
module miter(input [7:0] x, output bad);
wire [7:0] y0; wire [7:0] ref0 = x * 8'd3;
wire [7:0] y1; wire [7:0] ref1 = x * 8'd7;
wire [7:0] y2; wire [7:0] ref2 = x * 8'd21;
dut d(.x(x),.y0(y0),.y1(y1),.y2(y2));
assign bad = (|(y0 ^ ref0)) | (|(y1 ^ ref1)) | (|(y2 ^ ref2));
endmodule
