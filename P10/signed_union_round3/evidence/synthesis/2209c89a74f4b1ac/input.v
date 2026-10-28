module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = $signed(a) < 16'sd4;
wire [0:0] n1 = $signed(a) < -16'sd3;
wire [0:0] n2 = !n1;
wire [0:0] n3 = n0 && n2;
wire [2:0] z4 = b;
wire [2:0] n5 = z4;
wire [15:0] n6 = $signed(a) < 0 ? -a : a;
wire [15:0] n7 = {13'd0, n5} * n6;
wire [15:0] n8 = n7 + c;
wire [15:0] n9 = n8;
wire [15:0] n10 = n9;
wire [15:0] n11 = n10;
wire [15:0] n12 = n11;
wire [15:0] n13 = n12;
wire [15:0] n14 = n13;
wire [15:0] n15 = n3 ? n14 : c;
assign out = n15;
endmodule
