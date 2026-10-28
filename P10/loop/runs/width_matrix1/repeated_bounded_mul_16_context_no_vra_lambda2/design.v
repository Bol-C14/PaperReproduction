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
wire [2:0] n3 = n2;
wire [15:0] n4 = a;
wire [15:0] n5 = {13'd0, n3} * n4;
wire [15:0] n6 = n5;
wire [15:0] n7 = n6 + n6;
wire [15:0] n8 = n7;
wire [0:0] n9 = !n0;
wire [15:0] n10 = c;
wire [15:0] n11 = n10;
wire [15:0] n12 = n11;
wire [15:0] n13 = n0 ? n8 : n12;
assign out = n13;
endmodule
