module original(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = a < 16'd4;
wire [2:0] z1 = b;
wire [2:0] n2 = z1;
wire [15:0] n3 = a * {13'd0, n2};
wire [15:0] n4 = n3 + n3;
wire [15:0] n5 = n0 ? n4 : c;
assign out = n5;
endmodule
module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = a < 16'd4;
wire [2:0] z1 = b;
wire [2:0] n2 = z1;
wire [15:0] n3 = {13'd0, n2} * a;
wire [15:0] n4 = n3 + n3;
wire [15:0] n5 = n0 ? n4 : c;
assign out = n5;
endmodule
