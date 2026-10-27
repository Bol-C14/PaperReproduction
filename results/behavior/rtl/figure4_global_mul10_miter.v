module dut(input [7:0] x,output [7:0] y0);
assign y0 = (((((x << 1) << 1) + x) << 1) + x);
endmodule
module miter(input [7:0] x,output bad);
wire [7:0] y0; wire [7:0] r0 = (8'd11 * x);
dut d(.x(x),.y0(y0));
assign bad = (|(y0 ^ r0));
endmodule
