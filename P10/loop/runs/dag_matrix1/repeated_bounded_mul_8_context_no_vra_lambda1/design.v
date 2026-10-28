module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd4;
wire [2:0] z1 = b;
wire [2:0] n2 = z1;
wire [7:0] n3 = a * {5'd0, n2};
wire [7:0] n4 = n3 + n3;
wire [7:0] n5 = n0 ? n4 : c;
assign out = n5;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd4;
wire [7:0] n1 = a;
wire [7:0] n2 = n1;
wire [7:0] n3 = n2;
wire [2:0] z4 = b;
wire [2:0] n5 = z4;
wire [2:0] n6 = n5;
wire [2:0] n7 = n6;
wire [2:0] n8 = n7;
wire [7:0] n9 = n3 * {5'd0, n8};
wire [7:0] n10 = n9 + n9;
wire [0:0] n11 = !n0;
wire [7:0] n12 = c;
wire [7:0] n13 = n12;
wire [7:0] n14 = n13;
wire [7:0] n15 = n0 ? n10 : n14;
assign out = n15;
endmodule
