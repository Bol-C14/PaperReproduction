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
wire [2:0] n4 = n3;
wire [2:0] n5 = n4;
wire [15:0] n6 = a;
wire [15:0] n7 = n6;
wire [1:0] z8 = n7;
wire [1:0] n9 = z8;
wire [4:0] n10 = {2'd0, n5} * {3'd0, n9};
wire [15:0] n11 = {11'd0, n10};
wire [4:0] z12 = n11;
wire [4:0] n13 = z12;
wire [5:0] n14 = {1'd0, n13} + {1'd0, n13};
wire [15:0] n15 = {10'd0, n14};
wire [15:0] n16 = n0 ? n15 : c;
assign out = n16;
endmodule
