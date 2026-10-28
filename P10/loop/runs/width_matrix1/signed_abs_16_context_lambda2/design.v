module original(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = $signed(a) >= 0;
wire [15:0] n1 = $signed(a) < 0 ? -a : a;
wire [15:0] n2 = n1 + b;
wire [15:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = $signed(a) >= 0;
wire [15:0] n1 = b;
wire [15:0] n2 = a;
wire [15:0] n3 = n1 + n2;
wire [15:0] n4 = n3;
wire [15:0] n5 = n4;
wire [15:0] n6 = n5;
wire [15:0] n7 = n6;
wire [15:0] n8 = n7;
wire [15:0] n9 = n8;
wire [0:0] n10 = !n0;
wire [15:0] n11 = c;
wire [15:0] n12 = n11;
wire [15:0] n13 = n12;
wire [15:0] n14 = n13;
wire [15:0] n15 = n14;
wire [15:0] n16 = n15;
wire [15:0] n17 = n16;
wire [15:0] n18 = n0 ? n9 : n17;
assign out = n18;
endmodule
