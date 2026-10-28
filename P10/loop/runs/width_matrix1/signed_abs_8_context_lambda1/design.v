module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = $signed(a) >= 0;
wire [7:0] n1 = $signed(a) < 0 ? -a : a;
wire [7:0] n2 = n1 + b;
wire [7:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = $signed(a) >= 0;
wire [7:0] n1 = b;
wire [7:0] n2 = n1;
wire [7:0] n3 = a;
wire [6:0] z4 = n3;
wire [6:0] n5 = z4;
wire [7:0] n6 = n2 + {1'd0, n5};
wire [7:0] n7 = n6;
wire [7:0] n8 = n7;
wire [7:0] n9 = n8;
wire [0:0] n10 = !n0;
wire [7:0] n11 = c;
wire [7:0] n12 = n11;
wire [7:0] n13 = n12;
wire [7:0] n14 = n0 ? n9 : n13;
assign out = n14;
endmodule
