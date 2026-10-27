module dut(input [7:0] x,output [7:0] y0,output [7:0] y1,output [7:0] y2);
assign y0 = (8'd7 * x);
assign y1 = (8'd19 * x);
assign y2 = (((8'd15 * x) << 1) + x);
endmodule
module miter(input [7:0] x,output bad);
wire [7:0] y0; wire [7:0] r0 = (8'd7 * x);
wire [7:0] y1; wire [7:0] r1 = (8'd19 * x);
wire [7:0] y2; wire [7:0] r2 = (8'd31 * x);
dut d(.x(x),.y0(y0),.y1(y1),.y2(y2));
assign bad = (|(y0 ^ r0)) | (|(y1 ^ r1)) | (|(y2 ^ r2));
endmodule
