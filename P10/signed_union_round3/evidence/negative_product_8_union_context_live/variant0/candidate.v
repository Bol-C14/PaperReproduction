module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = $signed(a) < 8'sd0;
wire [0:0] n1 = $signed(a) < -8'sd4;
wire [0:0] n2 = !n1;
wire [0:0] n3 = n0 && n2;
wire [2:0] z4 = b;
wire [2:0] n5 = z4;
wire [2:0] n6 = n5;
wire [2:0] n7 = n6;
wire [7:0] n8 = $signed(a) < 0 ? -a : a;
wire [7:0] n9 = n8;
wire [2:0] z10 = n9;
wire [2:0] n11 = z10;
wire [4:0] n12 = {2'd0, n7} * {2'd0, n11};
wire [7:0] n13 = {3'd0, n12};
wire [7:0] n14 = n13;
wire [7:0] n15 = n3 ? n14 : c;
assign out = n15;
endmodule
