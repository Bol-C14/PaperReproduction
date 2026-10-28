module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd8;
wire [7:0] n1 = a * b;
wire [7:0] n2 = n1 + c;
wire [7:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd8;
wire [7:0] n1 = c;
wire [7:0] n2 = n1;
wire [7:0] n3 = n2;
wire [7:0] n4 = b;
wire [7:0] n5 = a;
wire [7:0] n6 = n4 * n5;
wire [7:0] n7 = n6;
wire [7:0] n8 = n7;
wire [7:0] n9 = n3 + n8;
wire [7:0] n10 = n9;
wire [7:0] n11 = n10;
wire [0:0] n12 = !n0;
wire [7:0] n13 = c;
wire [7:0] n14 = n13;
wire [7:0] n15 = n14;
wire [7:0] n16 = n15;
wire [7:0] n17 = n16;
wire [7:0] n18 = n0 ? n11 : n17;
assign out = n18;
endmodule
