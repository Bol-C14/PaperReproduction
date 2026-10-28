module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = $signed(a) < 16'sd4;
wire [0:0] n1 = $signed(a) < -16'sd3;
wire [0:0] n2 = !n1;
wire [0:0] n3 = n0 && n2;
wire [2:0] z4 = b;
wire [2:0] n5 = z4;
wire [2:0] n6 = n5;
wire [15:0] n7 = 16'd2 + a;
wire [15:0] n8 = $signed(n7) < 0 ? -n7 : n7;
wire [15:0] n9 = n8;
wire [15:0] n10 = {13'd0, n6} * n9;
wire [15:0] n11 = n10;
wire [15:0] n12 = n11;
wire [15:0] n13 = n3 ? n12 : c;
assign out = n13;
endmodule
