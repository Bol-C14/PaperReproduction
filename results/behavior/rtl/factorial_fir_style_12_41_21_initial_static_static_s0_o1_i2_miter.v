module dut(input [7:0] x0,input [7:0] x1,input [7:0] x2,output [7:0] y0);
assign y0 = (((8'd21 * x2) + (8'd12 * x0)) + (8'd41 * x1));
endmodule
module miter(input [7:0] x0,input [7:0] x1,input [7:0] x2,output bad);
wire [7:0] y0; wire [7:0] r0 = (((8'd12 * x0) + (8'd41 * x1)) + (8'd21 * x2));
dut d(.x0(x0),.x1(x1),.x2(x2),.y0(y0));
assign bad = (|(y0 ^ r0));
endmodule
