module original(input [15:0] a, input [15:0] b, input [15:0] c, input [15:0] y, output [15:0] out);
wire [0:0] n0 = y < 16'd2;
wire [15:0] n1 = a >> y;
wire [15:0] n2 = n1 + c;
wire [15:0] n3 = n0 ? n2 : b;
assign out = n3;
endmodule
module candidate(input [15:0] a, input [15:0] b, input [15:0] c, input [15:0] y, output [15:0] out);
wire [0:0] n0 = y < 16'd2;
wire [15:0] n1 = a;
wire [15:0] n2 = n1;
wire [15:0] n3 = n2;
wire [15:0] n4 = y;
wire [15:0] n5 = n4;
wire [15:0] n6 = n5;
wire [0:0] z7 = n6;
wire [0:0] n8 = z7;
wire [15:0] n9 = n3 >> n8;
wire [15:0] n10 = c;
wire [15:0] n11 = n10;
wire [15:0] n12 = n11;
wire [15:0] n13 = n9 + n12;
wire [0:0] n14 = !n0;
wire [15:0] n15 = b;
wire [15:0] n16 = n15;
wire [15:0] n17 = n16;
wire [15:0] n18 = n0 ? n13 : n17;
assign out = n18;
endmodule
