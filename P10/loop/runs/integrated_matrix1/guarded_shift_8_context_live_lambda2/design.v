module original(input [7:0] a, input [7:0] b, input [7:0] c, input [7:0] y, output [7:0] out);
wire [0:0] n0 = y < 8'd2;
wire [7:0] n1 = a >> y;
wire [7:0] n2 = n1 + c;
wire [7:0] n3 = n0 ? n2 : b;
assign out = n3;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [7:0] c, input [7:0] y, output [7:0] out);
wire [0:0] n0 = y < 8'd2;
wire [7:0] n1 = a;
wire [7:0] n2 = n1;
wire [7:0] n3 = y;
wire [7:0] n4 = n3;
wire [0:0] z5 = n4;
wire [0:0] n6 = z5;
wire [7:0] n7 = n2 >> n6;
wire [7:0] n8 = c;
wire [7:0] n9 = n8;
wire [7:0] n10 = n7 + n9;
wire [7:0] n11 = n10;
wire [7:0] n12 = n11;
wire [7:0] n13 = n12;
wire [7:0] n14 = n0 ? n13 : b;
assign out = n14;
endmodule
