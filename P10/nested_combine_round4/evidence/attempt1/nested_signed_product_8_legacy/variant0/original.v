module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = $signed(a) < 8'sd8;
wire [0:0] n1 = $signed(a) < -8'sd7;
wire [0:0] n2 = !n1;
wire [0:0] n3 = n0 && n2;
wire [0:0] n4 = $signed(a) < 8'sd0;
wire [7:0] n5 = -a;
wire [2:0] z6 = b;
wire [2:0] n7 = z6;
wire [7:0] n8 = n5 * {5'd0, n7};
wire [7:0] n9 = a * {5'd0, n7};
wire [7:0] n10 = n4 ? n8 : n9;
wire [7:0] n11 = n3 ? n10 : c;
assign out = n11;
endmodule
