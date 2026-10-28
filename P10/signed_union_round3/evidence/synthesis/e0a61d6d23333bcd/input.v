module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = $signed(a) < 16'sd4;
wire [0:0] n1 = $signed(a) < -16'sd3;
wire [0:0] n2 = !n1;
wire [0:0] n3 = n0 && n2;
wire [15:0] n4 = a;
wire [1:0] z5 = 16'd2;
wire [1:0] n6 = z5;
wire [15:0] n7 = n4 + {14'd0, n6};
wire [15:0] n8 = n7;
wire [15:0] n9 = $signed(n8) < 0 ? -n8 : n8;
wire [2:0] z10 = b;
wire [2:0] n11 = z10;
wire [15:0] n12 = n9 * {13'd0, n11};
wire [15:0] n13 = n3 ? n12 : c;
assign out = n13;
endmodule
