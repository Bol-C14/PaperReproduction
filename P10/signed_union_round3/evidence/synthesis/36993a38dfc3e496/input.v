module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = $signed(a) < 8'sd4;
wire [0:0] n1 = $signed(a) < -8'sd3;
wire [0:0] n2 = !n1;
wire [0:0] n3 = n0 && n2;
wire [7:0] n4 = c;
wire [7:0] n5 = n4;
wire [7:0] n6 = $signed(a) < 0 ? -a : a;
wire [2:0] z7 = b;
wire [2:0] n8 = z7;
wire [7:0] n9 = n6 * {5'd0, n8};
wire [7:0] n10 = n9;
wire [7:0] n11 = n10;
wire [7:0] n12 = n5 + n11;
wire [7:0] n13 = n3 ? n12 : c;
assign out = n13;
endmodule
