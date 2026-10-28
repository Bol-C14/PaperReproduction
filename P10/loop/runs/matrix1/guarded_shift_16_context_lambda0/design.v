module original(input [15:0] a, input [15:0] b, input [15:0] c, input [15:0] y, output [15:0] out);
wire [0:0] n0 = y < 16'd2;
wire [15:0] n1 = a >> y;
wire [15:0] n2 = n1 + c;
wire [15:0] n3 = n0 ? n2 : b;
assign out = n3;
endmodule
module candidate(input [15:0] a, input [15:0] b, input [15:0] c, input [15:0] y, output [15:0] out);
wire [0:0] n0 = y < 16'd2;
wire [15:0] n1 = a;
wire [15:0] n2 = y;
wire [0:0] z3 = n2;
wire [0:0] n4 = z3;
wire [15:0] n5 = n1 >> n4;
wire [15:0] n6 = c;
wire [15:0] n7 = n5 + n6;
wire [0:0] n8 = !n0;
wire [15:0] n9 = b;
wire [15:0] n10 = n0 ? n7 : n9;
assign out = n10;
endmodule
